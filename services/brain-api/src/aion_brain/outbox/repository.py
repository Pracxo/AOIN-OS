"""Persistence for transactional outbox messages."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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

from aion_brain.contracts.outbox import OutboxDestination, OutboxMessage, OutboxStatus

outbox_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_outbox_messages = Table(
    "aion_outbox_messages",
    outbox_metadata,
    Column("outbox_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("correlation_id", Text, nullable=True),
    Column("message_type", Text, nullable=False),
    Column("destination", Text, nullable=False),
    Column("subject", Text, nullable=True),
    Column("payload", json_payload_type, nullable=False),
    Column("headers", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("attempt_count", Integer, nullable=False),
    Column("max_attempts", Integer, nullable=False),
    Column("next_attempt_at", DateTime(timezone=True), nullable=True),
    Column("last_error", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("sent_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_outbox_trace_id", "trace_id"),
    Index("ix_aion_outbox_correlation_id", "correlation_id"),
    Index("ix_aion_outbox_message_type", "message_type"),
    Index("ix_aion_outbox_destination", "destination"),
    Index("ix_aion_outbox_subject", "subject"),
    Index("ix_aion_outbox_status", "status"),
    Index("ix_aion_outbox_next_attempt_at", "next_attempt_at"),
    Index("ix_aion_outbox_created_at", "created_at"),
)

aion_outbox_delivery_attempts = Table(
    "aion_outbox_delivery_attempts",
    outbox_metadata,
    Column("delivery_attempt_id", Text, primary_key=True),
    Column(
        "outbox_id",
        Text,
        ForeignKey("aion_outbox_messages.outbox_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("status", Text, nullable=False),
    Column("attempt_number", Integer, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("latency_ms", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_outbox_attempt_outbox_id", "outbox_id"),
    Index("ix_aion_outbox_attempt_status", "status"),
    Index("ix_aion_outbox_attempt_number", "attempt_number"),
    Index("ix_aion_outbox_attempt_created_at", "created_at"),
)


class OutboxRepository:
    """Repository for transactional outbox messages."""

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

    def save(self, message: OutboxMessage) -> OutboxMessage:
        """Create or replace one outbox message."""
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = message.model_copy(
            update={
                "created_at": message.created_at or now,
                "updated_at": now,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_outbox_messages).where(
                    aion_outbox_messages.c.outbox_id == stored.outbox_id
                )
            )
            connection.execute(
                insert(aion_outbox_messages).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get(self, outbox_id: str) -> OutboxMessage | None:
        """Return one outbox message."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_outbox_messages).where(
                        aion_outbox_messages.c.outbox_id == outbox_id
                    )
                )
                .mappings()
                .first()
            )
        return None if row is None else _row_to_message(row)

    def list_messages(
        self,
        *,
        status: str | None = None,
        destination: str | None = None,
        limit: int = 50,
    ) -> list[OutboxMessage]:
        """List recent messages."""
        self._ensure_schema()
        statement = (
            select(aion_outbox_messages).order_by(aion_outbox_messages.c.created_at).limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_outbox_messages.c.status == status)
        if destination is not None:
            statement = statement.where(aion_outbox_messages.c.destination == destination)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_message(row) for row in rows]

    def save_attempt(
        self,
        *,
        delivery_attempt_id: str,
        outbox_id: str,
        status: str,
        attempt_number: int,
        error: dict[str, Any],
        latency_ms: int | None = None,
    ) -> None:
        """Append one delivery attempt."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_outbox_delivery_attempts).values(
                    delivery_attempt_id=delivery_attempt_id,
                    outbox_id=outbox_id,
                    status=status,
                    attempt_number=attempt_number,
                    error=error,
                    latency_ms=latency_ms,
                    created_at=datetime.now(UTC),
                )
            )

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        outbox_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _row_to_message(row: RowMapping) -> OutboxMessage:
    return OutboxMessage(
        outbox_id=str(row["outbox_id"]),
        trace_id=_optional_str(row["trace_id"]),
        correlation_id=_optional_str(row["correlation_id"]),
        message_type=str(row["message_type"]),
        destination=cast(OutboxDestination, str(row["destination"])),
        subject=_optional_str(row["subject"]),
        payload=_dict(row["payload"]),
        headers=_dict(row["headers"]),
        status=cast(OutboxStatus, str(row["status"])),
        attempt_count=int(row["attempt_count"]),
        max_attempts=int(row["max_attempts"]),
        next_attempt_at=_optional_datetime(row["next_attempt_at"]),
        last_error=_dict(row["last_error"]),
        created_at=_datetime(row["created_at"]),
        sent_at=_optional_datetime(row["sent_at"]),
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
