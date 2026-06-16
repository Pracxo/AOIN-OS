"""Persistence and query repository for Visual Brain Projection."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
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
from sqlalchemy.pool import QueuePool

from aion_brain.audit.repository import aion_visual_telemetry, audit_metadata
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.contracts.visual import (
    BrainMap,
    BrainMapSnapshot,
    BrainVisualStatus,
    TraceTimeline,
    VisualTelemetryQuery,
)

visual_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_brain_map_snapshots = Table(
    "aion_brain_map_snapshots",
    visual_metadata,
    Column("snapshot_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("map", json_payload_type, nullable=False),
    Column("node_count", Integer, nullable=False),
    Column("edge_count", Integer, nullable=False),
    Column("pulse_count", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_brain_map_snapshots_trace_id", "trace_id"),
    Index("ix_aion_brain_map_snapshots_workspace_id", "workspace_id"),
    Index("ix_aion_brain_map_snapshots_created_at", "created_at"),
)

aion_trace_timeline_records = Table(
    "aion_trace_timeline_records",
    visual_metadata,
    Column("timeline_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("events", json_payload_type, nullable=False),
    Column("duration_ms", Integer, nullable=True),
    Column("status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_trace_timeline_records_trace_id", "trace_id"),
    Index("ix_aion_trace_timeline_records_status", "status"),
    Index("ix_aion_trace_timeline_records_created_at", "created_at"),
)


class VisualRepository:
    """Repository for telemetry reads and visual projection records."""

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

    def query_telemetry(self, query: VisualTelemetryQuery) -> list[VisualTelemetryEvent]:
        """Query telemetry and apply scope-aware filters."""
        self._ensure_schema()
        statement = select(aion_visual_telemetry)
        if query.trace_id:
            statement = statement.where(aion_visual_telemetry.c.trace_id == query.trace_id)
        if query.event_types:
            statement = statement.where(aion_visual_telemetry.c.event_type.in_(query.event_types))
        if query.node_types:
            statement = statement.where(aion_visual_telemetry.c.node_type.in_(query.node_types))
        if query.since:
            statement = statement.where(aion_visual_telemetry.c.created_at >= query.since)
        if query.until:
            statement = statement.where(aion_visual_telemetry.c.created_at <= query.until)
        statement = statement.order_by(aion_visual_telemetry.c.created_at.desc()).limit(query.limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        events = [_row_to_telemetry(row) for row in rows]
        return [
            event
            for event in events
            if _event_in_scope(event, query.scope) and _workspace_matches(event, query.workspace_id)
        ][: query.limit]

    def count_telemetry(self, scope: list[str]) -> int:
        """Count accessible telemetry events."""
        return len(
            self.query_telemetry(
                VisualTelemetryQuery(scope=scope, limit=1000),
            )
        )

    def save_snapshot(self, snapshot: BrainMapSnapshot) -> BrainMapSnapshot:
        """Persist a Brain Map snapshot."""
        self._ensure_schema()
        stored = snapshot.model_copy(
            update={"created_at": snapshot.created_at or datetime.now(UTC)}
        )
        values = stored.model_dump(mode="python", exclude={"map"})
        values["map"] = stored.map.model_dump(mode="json")
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_brain_map_snapshots).where(
                    aion_brain_map_snapshots.c.snapshot_id == stored.snapshot_id
                )
            )
            connection.execute(insert(aion_brain_map_snapshots).values(**values))
        return stored

    def get_snapshot(self, snapshot_id: str) -> BrainMapSnapshot | None:
        """Return a persisted Brain Map snapshot."""
        self._ensure_schema()
        statement = select(aion_brain_map_snapshots).where(
            aion_brain_map_snapshots.c.snapshot_id == snapshot_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _row_to_snapshot(row)

    def save_timeline(self, timeline: TraceTimeline) -> TraceTimeline:
        """Persist a trace timeline projection."""
        self._ensure_schema()
        values = timeline.model_dump(mode="python", exclude={"events"})
        values["events"] = [event.model_dump(mode="json") for event in timeline.events]
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_trace_timeline_records).where(
                    aion_trace_timeline_records.c.timeline_id == timeline.timeline_id
                )
            )
            connection.execute(insert(aion_trace_timeline_records).values(**values))
        return timeline

    def get_timeline(self, trace_id: str) -> TraceTimeline | None:
        """Return the latest persisted timeline for a trace."""
        self._ensure_schema()
        statement = (
            select(aion_trace_timeline_records)
            .where(aion_trace_timeline_records.c.trace_id == trace_id)
            .order_by(aion_trace_timeline_records.c.created_at.desc())
            .limit(1)
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        return _row_to_timeline(row)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        audit_metadata.create_all(self._engine)
        visual_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_telemetry(row: RowMapping) -> VisualTelemetryEvent:
    return VisualTelemetryEvent(
        telemetry_id=str(row["telemetry_id"]),
        trace_id=str(row["trace_id"]),
        event_type=cast(VisualTelemetryEventType, str(row["event_type"])),
        node_type=cast(VisualNodeType, str(row["node_type"])),
        node_id=str(row["node_id"]),
        edge_from=_optional_str(row["edge_from"]),
        edge_to=_optional_str(row["edge_to"]),
        intensity=float(row["intensity"]),
        payload=dict(row["payload"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_snapshot(row: RowMapping) -> BrainMapSnapshot:
    return BrainMapSnapshot(
        snapshot_id=str(row["snapshot_id"]),
        trace_id=_optional_str(row["trace_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_string_list(row["owner_scope"]),
        map=BrainMap.model_validate(row["map"]),
        node_count=int(row["node_count"]),
        edge_count=int(row["edge_count"]),
        pulse_count=int(row["pulse_count"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_timeline(row: RowMapping) -> TraceTimeline:
    return TraceTimeline(
        timeline_id=str(row["timeline_id"]),
        trace_id=str(row["trace_id"]),
        owner_scope=_string_list(row["owner_scope"]),
        events=list(row["events"]),
        duration_ms=int(row["duration_ms"]) if row["duration_ms"] is not None else None,
        status=cast(BrainVisualStatus, str(row["status"])),
        created_at=_datetime(row["created_at"]),
    )


def _event_in_scope(event: VisualTelemetryEvent, requested_scope: list[str]) -> bool:
    event_scope = _payload_scope(event.payload)
    return not event_scope or bool(set(event_scope) & set(requested_scope))


def _workspace_matches(event: VisualTelemetryEvent, workspace_id: str | None) -> bool:
    if workspace_id is None:
        return True
    return event.payload.get("workspace_id") in {None, workspace_id}


def _payload_scope(payload: dict[str, Any]) -> list[str]:
    for key in ("owner_scope", "security_scope", "resolved_security_scope"):
        value = payload.get(key)
        if isinstance(value, list):
            return [str(item) for item in value]
    return []


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError("Expected datetime-compatible value")
