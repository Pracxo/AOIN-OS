"""Persistence for processing leases and consistency checks."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    MetaData,
    Table,
    Text,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.consistency import (
    ConsistencyCheckResult,
    ConsistencyCheckStatus,
    ConsistencyCheckType,
    LeaseStatus,
    ProcessingLease,
)

consistency_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_processing_leases = Table(
    "aion_processing_leases",
    consistency_metadata,
    Column("lease_id", Text, primary_key=True),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("owner_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("released_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_leases_resource_type", "resource_type"),
    Index("ix_aion_leases_resource_id", "resource_id"),
    Index("ix_aion_leases_owner_id", "owner_id"),
    Index("ix_aion_leases_status", "status"),
    Index("ix_aion_leases_expires_at", "expires_at"),
    Index("ix_aion_leases_created_at", "created_at"),
)

aion_consistency_checks = Table(
    "aion_consistency_checks",
    consistency_metadata,
    Column("consistency_check_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("check_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("scope", json_payload_type, nullable=False),
    Column("violations", json_payload_type, nullable=False),
    Column("repaired", Boolean, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_consistency_trace_id", "trace_id"),
    Index("ix_aion_consistency_check_type", "check_type"),
    Index("ix_aion_consistency_status", "status"),
    Index("ix_aion_consistency_repaired", "repaired"),
    Index("ix_aion_consistency_created_at", "created_at"),
)


class ConsistencyRepository:
    """Repository for consistency records."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            self._engine = _create_engine(database_url)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_lease(self, lease: ProcessingLease) -> ProcessingLease:
        """Create or replace one processing lease."""
        self._ensure_schema()
        stored = lease.model_copy(update={"created_at": lease.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_processing_leases).where(
                    aion_processing_leases.c.lease_id == stored.lease_id
                )
            )
            connection.execute(
                insert(aion_processing_leases).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_lease(self, lease_id: str) -> ProcessingLease | None:
        """Return one lease by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_processing_leases).where(
                        aion_processing_leases.c.lease_id == lease_id
                    )
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_lease(row)

    def get_active_lease(self, resource_type: str, resource_id: str) -> ProcessingLease | None:
        """Return active lease for a resource."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_processing_leases)
                    .where(aion_processing_leases.c.resource_type == resource_type)
                    .where(aion_processing_leases.c.resource_id == resource_id)
                    .where(aion_processing_leases.c.status == "active")
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_lease(row)

    def list_leases(self, *, status: str | None = None, limit: int = 100) -> list[ProcessingLease]:
        """List leases."""
        self._ensure_schema()
        statement = (
            select(aion_processing_leases)
            .order_by(aion_processing_leases.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_processing_leases.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_lease(row) for row in rows]

    def save_check(self, result: ConsistencyCheckResult) -> ConsistencyCheckResult:
        """Persist a consistency check result."""
        self._ensure_schema()
        stored = result.model_copy(update={"created_at": result.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_consistency_checks).where(
                    aion_consistency_checks.c.consistency_check_id == stored.consistency_check_id
                )
            )
            connection.execute(
                insert(aion_consistency_checks).values(**stored.model_dump(mode="python"))
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        consistency_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _row_to_lease(row: RowMapping) -> ProcessingLease:
    return ProcessingLease(
        lease_id=str(row["lease_id"]),
        resource_type=str(row["resource_type"]),
        resource_id=str(row["resource_id"]),
        owner_id=str(row["owner_id"]),
        status=cast(LeaseStatus, str(row["status"])),
        expires_at=_datetime(row["expires_at"]),
        metadata=_dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
        released_at=_optional_datetime(row["released_at"]),
    )


def _row_to_check(row: RowMapping) -> ConsistencyCheckResult:
    return ConsistencyCheckResult(
        consistency_check_id=str(row["consistency_check_id"]),
        trace_id=_optional_str(row["trace_id"]),
        check_type=cast(ConsistencyCheckType, str(row["check_type"])),
        status=cast(ConsistencyCheckStatus, str(row["status"])),
        scope=[str(item) for item in _list(row["scope"])],
        violations=[dict(item) for item in _list(row["violations"]) if isinstance(item, dict)],
        repaired=bool(row["repaired"]),
        result=_dict(row["result"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    raise TypeError("Expected datetime-compatible value")
