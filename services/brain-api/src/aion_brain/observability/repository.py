"""Local observability event repository."""

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
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.observability import ObservabilityEvent, ObservabilityLevel

observability_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_observability_events = Table(
    "aion_observability_events",
    observability_metadata,
    Column("observability_event_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("correlation_id", Text, nullable=True),
    Column("event_type", Text, nullable=False),
    Column("component", Text, nullable=False),
    Column("level", Text, nullable=False),
    Column("message", Text, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_observability_events_trace_id", "trace_id"),
    Index("ix_aion_observability_events_correlation_id", "correlation_id"),
    Index("ix_aion_observability_events_event_type", "event_type"),
    Index("ix_aion_observability_events_component", "component"),
    Index("ix_aion_observability_events_level", "level"),
    Index("ix_aion_observability_events_created_at", "created_at"),
)


class ObservabilityRepository:
    """Persist and query sanitized local observability events."""

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
            self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save(self, event: ObservabilityEvent) -> ObservabilityEvent:
        """Persist an observability event."""
        self._ensure_schema()
        stored = event.model_copy(update={"created_at": event.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_observability_events).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_events(self, limit: int = 1000) -> list[ObservabilityEvent]:
        """Return recent observability events."""
        self._ensure_schema()
        statement = select(aion_observability_events).order_by(
            aion_observability_events.c.created_at.desc()
        ).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_event(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        observability_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_event(row: RowMapping) -> ObservabilityEvent:
    return ObservabilityEvent(
        observability_event_id=str(row["observability_event_id"]),
        trace_id=_optional_str(row["trace_id"]),
        correlation_id=_optional_str(row["correlation_id"]),
        event_type=str(row["event_type"]),
        component=str(row["component"]),
        level=cast(ObservabilityLevel, str(row["level"])),
        message=str(row["message"]),
        payload=dict(row["payload"]),
        created_at=_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError("Expected datetime-compatible value")
