"""Persistence for inbox deduplication records."""

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
    UniqueConstraint,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.inbox import InboxMessage, InboxStatus

inbox_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_inbox_messages = Table(
    "aion_inbox_messages",
    inbox_metadata,
    Column("inbox_id", Text, primary_key=True),
    Column("source", Text, nullable=False),
    Column("external_message_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("correlation_id", Text, nullable=True),
    Column("message_type", Text, nullable=False),
    Column("payload_hash", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("processed_by", Text, nullable=True),
    Column("result", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("received_at", DateTime(timezone=True), nullable=False),
    Column("processed_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("source", "external_message_id", name="uq_aion_inbox_source_message"),
    Index("ix_aion_inbox_source", "source"),
    Index("ix_aion_inbox_external_message_id", "external_message_id"),
    Index("ix_aion_inbox_trace_id", "trace_id"),
    Index("ix_aion_inbox_correlation_id", "correlation_id"),
    Index("ix_aion_inbox_message_type", "message_type"),
    Index("ix_aion_inbox_status", "status"),
    Index("ix_aion_inbox_received_at", "received_at"),
)


class InboxRepository:
    """Repository for inbox messages."""

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

    def save(self, message: InboxMessage) -> InboxMessage:
        """Create or replace one inbox record."""
        self._ensure_schema()
        stored = message.model_copy(
            update={"received_at": message.received_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_inbox_messages).where(aion_inbox_messages.c.inbox_id == stored.inbox_id)
            )
            connection.execute(
                insert(aion_inbox_messages).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get(self, inbox_id: str) -> InboxMessage | None:
        """Return one inbox message."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_inbox_messages).where(aion_inbox_messages.c.inbox_id == inbox_id)
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_message(row)

    def get_by_external_id(self, source: str, external_message_id: str) -> InboxMessage | None:
        """Return one inbox message by external identity."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_inbox_messages)
                    .where(aion_inbox_messages.c.source == source)
                    .where(aion_inbox_messages.c.external_message_id == external_message_id)
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_message(row)

    def list_messages(
        self,
        *,
        status: str | None = None,
        source: str | None = None,
        limit: int = 50,
    ) -> list[InboxMessage]:
        """List inbox messages."""
        self._ensure_schema()
        statement = (
            select(aion_inbox_messages)
            .order_by(aion_inbox_messages.c.received_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_inbox_messages.c.status == status)
        if source is not None:
            statement = statement.where(aion_inbox_messages.c.source == source)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_message(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        inbox_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _row_to_message(row: RowMapping) -> InboxMessage:
    return InboxMessage(
        inbox_id=str(row["inbox_id"]),
        source=str(row["source"]),
        external_message_id=str(row["external_message_id"]),
        trace_id=_optional_str(row["trace_id"]),
        correlation_id=_optional_str(row["correlation_id"]),
        message_type=str(row["message_type"]),
        payload_hash=str(row["payload_hash"]),
        status=cast(InboxStatus, str(row["status"])),
        processed_by=_optional_str(row["processed_by"]),
        result=_dict(row["result"]),
        error=_dict(row["error"]),
        received_at=_datetime(row["received_at"]),
        processed_at=_optional_datetime(row["processed_at"]),
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
