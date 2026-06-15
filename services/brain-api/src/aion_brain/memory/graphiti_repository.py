"""Graphiti adapter metadata repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, TypedDict, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.graph import GraphitiConfigStatus

graphiti_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_graphiti_configs = Table(
    "aion_graphiti_configs",
    graphiti_metadata,
    Column("graphiti_config_id", Text, primary_key=True),
    Column("config_name", Text, nullable=False),
    Column("adapter_name", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("backend_type", Text, nullable=False),
    Column("endpoint_ref", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_health_check_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_graphiti_configs_config_name", "config_name"),
    Index("ix_aion_graphiti_configs_adapter_name", "adapter_name"),
    Index("ix_aion_graphiti_configs_status", "status"),
    Index("ix_aion_graphiti_configs_backend_type", "backend_type"),
    Index("ix_aion_graphiti_configs_created_at", "created_at"),
)

aion_graphiti_sync_records = Table(
    "aion_graphiti_sync_records",
    graphiti_metadata,
    Column("sync_id", Text, primary_key=True),
    Column(
        "graphiti_config_id",
        Text,
        ForeignKey("aion_graphiti_configs.graphiti_config_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_graphiti_sync_records_graphiti_config_id", "graphiti_config_id"),
    Index("ix_aion_graphiti_sync_records_source_type", "source_type"),
    Index("ix_aion_graphiti_sync_records_source_id", "source_id"),
    Index("ix_aion_graphiti_sync_records_target_type", "target_type"),
    Index("ix_aion_graphiti_sync_records_target_id", "target_id"),
    Index("ix_aion_graphiti_sync_records_status", "status"),
    Index("ix_aion_graphiti_sync_records_deleted_at", "deleted_at"),
    Index("ix_aion_graphiti_sync_records_created_at", "created_at"),
)


class GraphitiSyncRecord(TypedDict):
    """AION-owned typed sync metadata row."""

    sync_id: str
    graphiti_config_id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    status: str
    owner_scope: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class GraphitiRepository:
    """Repository for optional Graphiti adapter metadata."""

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
            if database_url.startswith("sqlite"):
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(
                    database_url,
                    poolclass=QueuePool,
                    pool_pre_ping=True,
                )
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def create_or_get_config(
        self,
        config_name: str,
        backend_type: str,
        endpoint_ref: str | None,
    ) -> GraphitiConfigStatus:
        """Create or return a Graphiti config status."""
        self._ensure_schema()
        existing = self.get_config(config_name)
        if existing is not None:
            return existing
        now = datetime.now(UTC)
        status = GraphitiConfigStatus(
            graphiti_config_id=f"graphiti-{config_name}",
            config_name=config_name,
            adapter_name="graphiti",
            status="active",
            backend_type=cast(Any, backend_type),
            endpoint_ref=endpoint_ref,
            available=True,
            reason=None,
            metadata={},
            created_at=now,
            updated_at=now,
            last_health_check_at=None,
        )
        values = _status_values(status)
        with self._engine.begin() as connection:
            connection.execute(insert(aion_graphiti_configs).values(**values))
        return status

    def get_config(self, config_name: str) -> GraphitiConfigStatus | None:
        """Return a Graphiti config status by name."""
        self._ensure_schema()
        statement = select(aion_graphiti_configs).where(
            aion_graphiti_configs.c.config_name == config_name
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _status_from_row(row)

    def update_config_status(
        self,
        config_id: str,
        status: str,
        reason: str | None = None,
    ) -> GraphitiConfigStatus:
        """Update and return a config status."""
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_graphiti_configs)
                .where(aion_graphiti_configs.c.graphiti_config_id == config_id)
                .values(
                    status=status,
                    metadata={"reason": reason} if reason else {},
                    updated_at=now,
                    last_health_check_at=now,
                )
            )
        found = self._get_config_by_id(config_id)
        if found is None:
            raise KeyError(config_id)
        return found

    def record_sync(
        self,
        config_id: str,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        owner_scope: list[str],
        status: str,
        metadata: dict[str, Any],
    ) -> None:
        """Record sync metadata for one Graphiti target."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = {
            "sync_id": f"sync-{config_id}-{source_type}-{source_id}",
            "graphiti_config_id": config_id,
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "status": status,
            "owner_scope": owner_scope,
            "metadata": metadata,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_graphiti_sync_records).where(
                    aion_graphiti_sync_records.c.sync_id == values["sync_id"]
                )
            ).mappings().first()
            if existing is None:
                connection.execute(insert(aion_graphiti_sync_records).values(**values))
            else:
                connection.execute(
                    update(aion_graphiti_sync_records)
                    .where(aion_graphiti_sync_records.c.sync_id == values["sync_id"])
                    .values(**values)
                )

    def list_sync_records(
        self,
        config_id: str,
        scope: list[str],
        source_type: str | None = None,
        limit: int = 10000,
    ) -> list[GraphitiSyncRecord]:
        """List active sync records visible to scope."""
        self._ensure_schema()
        statement = select(aion_graphiti_sync_records).where(
            aion_graphiti_sync_records.c.graphiti_config_id == config_id,
            aion_graphiti_sync_records.c.deleted_at.is_(None),
        )
        if source_type is not None:
            statement = statement.where(aion_graphiti_sync_records.c.source_type == source_type)
        statement = statement.order_by(aion_graphiti_sync_records.c.created_at.desc())
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        records = [
            _sync_from_row(row)
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
        ]
        return records[:limit]

    def soft_delete_sync_record(
        self,
        config_id: str,
        source_type: str,
        source_id: str,
    ) -> bool:
        """Soft-delete one sync record by source."""
        self._ensure_schema()
        statement = (
            update(aion_graphiti_sync_records)
            .where(
                aion_graphiti_sync_records.c.graphiti_config_id == config_id,
                aion_graphiti_sync_records.c.source_type == source_type,
                aion_graphiti_sync_records.c.source_id == source_id,
                aion_graphiti_sync_records.c.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return result.rowcount > 0

    def _get_config_by_id(self, config_id: str) -> GraphitiConfigStatus | None:
        statement = select(aion_graphiti_configs).where(
            aion_graphiti_configs.c.graphiti_config_id == config_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _status_from_row(row)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        graphiti_metadata.create_all(self._engine)
        self._schema_ready = True


def _status_values(status: GraphitiConfigStatus) -> dict[str, Any]:
    return status.model_dump(mode="python", exclude={"available", "reason"})


def _status_from_row(row: RowMapping) -> GraphitiConfigStatus:
    metadata = dict(row["metadata"])
    reason = metadata.get("reason")
    return GraphitiConfigStatus(
        graphiti_config_id=str(row["graphiti_config_id"]),
        config_name=str(row["config_name"]),
        adapter_name=str(row["adapter_name"]),
        status=cast(Any, str(row["status"])),
        backend_type=cast(Any, str(row["backend_type"])),
        endpoint_ref=_optional_str(row["endpoint_ref"]),
        available=str(row["status"]) == "active",
        reason=str(reason) if reason else None,
        metadata=metadata,
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        last_health_check_at=_optional_datetime(row["last_health_check_at"]),
    )


def _sync_from_row(row: RowMapping) -> GraphitiSyncRecord:
    return GraphitiSyncRecord(
        sync_id=str(row["sync_id"]),
        graphiti_config_id=str(row["graphiti_config_id"]),
        source_type=str(row["source_type"]),
        source_id=str(row["source_id"]),
        target_type=str(row["target_type"]),
        target_id=str(row["target_id"]),
        status=str(row["status"]),
        owner_scope=list(row["owner_scope"]),
        metadata=dict(row["metadata"]),
        created_at=_coerce_datetime(row["created_at"]),
        updated_at=_coerce_datetime(row["updated_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return "*" in requested_scope or bool(set(record_scope).intersection(requested_scope))


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
