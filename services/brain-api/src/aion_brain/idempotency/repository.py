"""Persistence for idempotency records."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
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

from aion_brain.contracts.idempotency import IdempotencyRecord, IdempotencyStatus

idempotency_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_idempotency_records = Table(
    "aion_idempotency_records",
    idempotency_metadata,
    Column("idempotency_key", Text, primary_key=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("route", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column("response_hash", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("response", json_payload_type, nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_idempotency_actor_id", "actor_id"),
    Index("ix_aion_idempotency_workspace_id", "workspace_id"),
    Index("ix_aion_idempotency_route", "route"),
    Index("ix_aion_idempotency_request_hash", "request_hash"),
    Index("ix_aion_idempotency_status", "status"),
    Index("ix_aion_idempotency_expires_at", "expires_at"),
    Index("ix_aion_idempotency_created_at", "created_at"),
)


class IdempotencyRepository:
    """Repository for idempotency records."""

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

    def save(self, record: IdempotencyRecord) -> IdempotencyRecord:
        """Create or replace one idempotency record."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = record.model_copy(
            update={
                "created_at": record.created_at or now,
                "updated_at": now,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_idempotency_records).where(
                    aion_idempotency_records.c.idempotency_key == stored.idempotency_key
                )
            )
            connection.execute(
                insert(aion_idempotency_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get(self, idempotency_key: str) -> IdempotencyRecord | None:
        """Return one record by idempotency key."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_idempotency_records).where(
                        aion_idempotency_records.c.idempotency_key == idempotency_key
                    )
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_record(row)

    def expire_old(self, now: datetime, limit: int) -> int:
        """Mark expired records as expired."""
        self._ensure_schema()
        statement = (
            select(aion_idempotency_records)
            .where(aion_idempotency_records.c.status != "expired")
            .where(aion_idempotency_records.c.expires_at.is_not(None))
            .where(aion_idempotency_records.c.expires_at <= now)
            .limit(limit)
        )
        expired = 0
        with self._engine.begin() as connection:
            rows = connection.execute(statement).mappings().all()
            for row in rows:
                record = _row_to_record(row).model_copy(update={"status": "expired"})
                connection.execute(
                    delete(aion_idempotency_records).where(
                        aion_idempotency_records.c.idempotency_key == record.idempotency_key
                    )
                )
                connection.execute(
                    insert(aion_idempotency_records).values(**record.model_dump(mode="python"))
                )
                expired += 1
        return expired

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        idempotency_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _row_to_record(row: RowMapping) -> IdempotencyRecord:
    return IdempotencyRecord(
        idempotency_key=str(row["idempotency_key"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        route=str(row["route"]),
        request_hash=str(row["request_hash"]),
        response_hash=_optional_str(row["response_hash"]),
        status=cast(IdempotencyStatus, str(row["status"])),
        response=_dict(row["response"]),
        expires_at=_optional_datetime(row["expires_at"]),
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
    )


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
