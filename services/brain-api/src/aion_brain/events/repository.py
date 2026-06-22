"""Persistent event ledger repository."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.events import AIONEvent

metadata = MetaData()

json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_events = Table(
    "aion_events",
    metadata,
    Column("event_id", Text, primary_key=True),
    Column("source", Text, nullable=False),
    Column("event_type", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("payload_type", Text, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("correlation_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("security_scope", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_events_event_type", "event_type"),
    Index("ix_aion_events_workspace_id", "workspace_id"),
    Index("ix_aion_events_trace_id", "trace_id"),
    Index("ix_aion_events_timestamp", "timestamp"),
    Index("ix_aion_events_correlation_id", "correlation_id"),
)


class EventRepository:
    """Repository for the canonical AION event ledger."""

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
            self._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_pre_ping=True,
            )
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False
        self._audit_sink: object | None = None

    def set_audit_sink(self, audit_sink: object | None) -> None:
        """Attach audit sink after kernel assembly."""
        self._audit_sink = audit_sink

    def save(self, event: AIONEvent) -> AIONEvent:
        """Persist an event and return the stored contract."""
        self._ensure_schema()
        values = event.model_dump(mode="python")
        values["created_at"] = datetime.now(UTC)

        with self._engine.begin() as connection:
            connection.execute(insert(aion_events).values(**values))

        record_audit_event(
            self._audit_sink,
            action_type="event.ingest",
            resource_type="event",
            resource_id=event.event_id,
            event_type="event_accepted",
            outcome="completed",
            source_component="event_repository",
            trace_id=event.trace_id,
            correlation_id=event.correlation_id,
            actor_id=event.actor_id,
            workspace_id=event.workspace_id,
            payload={
                "source": event.source,
                "event_type": event.event_type,
                "payload_type": event.payload_type,
                "payload": event.payload,
            },
        )
        return event

    def get(self, event_id: str) -> AIONEvent | None:
        """Return an event by ID, if present."""
        self._ensure_schema()
        statement = select(aion_events).where(aion_events.c.event_id == event_id)

        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()

        if row is None:
            return None
        return self._row_to_event(row)

    def list_by_trace(self, trace_id: str) -> list[AIONEvent]:
        """Return events that belong to a trace."""
        self._ensure_schema()
        statement = (
            select(aion_events)
            .where(aion_events.c.trace_id == trace_id)
            .order_by(aion_events.c.timestamp)
        )

        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        return [self._row_to_event(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return

        metadata.create_all(self._engine)
        self._schema_ready = True

    def _row_to_event(self, row: RowMapping) -> AIONEvent:
        return AIONEvent(
            event_id=str(row["event_id"]),
            source=str(row["source"]),
            event_type=str(row["event_type"]),
            actor_id=_optional_str(row["actor_id"]),
            workspace_id=_optional_str(row["workspace_id"]),
            payload_type=str(row["payload_type"]),
            payload=dict(row["payload"]),
            timestamp=_coerce_datetime(row["timestamp"]),
            correlation_id=_optional_str(row["correlation_id"]),
            trace_id=_optional_str(row["trace_id"]),
            security_scope=list(row["security_scope"]),
        )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
