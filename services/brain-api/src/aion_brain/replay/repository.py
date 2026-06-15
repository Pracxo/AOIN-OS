"""Persistent repositories for Brain snapshots and replay runs."""

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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.replay import (
    BrainSnapshot,
    ReplayMode,
    ReplayRun,
    ReplayStatus,
    SnapshotType,
)

replay_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_brain_snapshots = Table(
    "aion_brain_snapshots",
    replay_metadata,
    Column("snapshot_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("snapshot_type", Text, nullable=False),
    Column("state", json_payload_type, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_brain_snapshots_trace_id", "trace_id"),
    Index("ix_aion_brain_snapshots_workspace_id", "workspace_id"),
    Index("ix_aion_brain_snapshots_snapshot_type", "snapshot_type"),
    Index("ix_aion_brain_snapshots_content_hash", "content_hash"),
    Index("ix_aion_brain_snapshots_created_at", "created_at"),
)

aion_replay_runs = Table(
    "aion_replay_runs",
    replay_metadata,
    Column("replay_id", Text, primary_key=True),
    Column("source_trace_id", Text, nullable=False),
    Column("replay_trace_id", Text, nullable=True),
    Column("mode", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("input_snapshot_id", Text, nullable=True),
    Column("output_snapshot_id", Text, nullable=True),
    Column("comparison", json_payload_type, nullable=False),
    Column("drift_detected", Boolean, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_replay_runs_source_trace_id", "source_trace_id"),
    Index("ix_aion_replay_runs_replay_trace_id", "replay_trace_id"),
    Index("ix_aion_replay_runs_mode", "mode"),
    Index("ix_aion_replay_runs_status", "status"),
    Index("ix_aion_replay_runs_drift_detected", "drift_detected"),
    Index("ix_aion_replay_runs_created_at", "created_at"),
)


class ReplayRepository:
    """Store content-addressed snapshots and replay outcomes."""

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

    def save_snapshot(self, snapshot: BrainSnapshot) -> BrainSnapshot:
        """Persist and return a Brain snapshot."""
        self._ensure_schema()
        stored = snapshot.model_copy(
            update={"created_at": snapshot.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_brain_snapshots).where(
                    aion_brain_snapshots.c.snapshot_id == stored.snapshot_id
                )
            )
            connection.execute(insert(aion_brain_snapshots).values(**stored.model_dump(mode="python")))
        return stored

    def get_snapshot(self, snapshot_id: str) -> BrainSnapshot | None:
        """Return a snapshot by ID."""
        self._ensure_schema()
        statement = select(aion_brain_snapshots).where(
            aion_brain_snapshots.c.snapshot_id == snapshot_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_snapshot(row) if row is not None else None

    def list_snapshots(
        self,
        *,
        trace_id: str | None = None,
        snapshot_type: str | None = None,
        limit: int = 50,
    ) -> list[BrainSnapshot]:
        """Return recent snapshots matching canonical fields."""
        self._ensure_schema()
        statement = select(aion_brain_snapshots)
        if trace_id:
            statement = statement.where(aion_brain_snapshots.c.trace_id == trace_id)
        if snapshot_type:
            statement = statement.where(aion_brain_snapshots.c.snapshot_type == snapshot_type)
        statement = statement.order_by(aion_brain_snapshots.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_snapshot(row) for row in rows]

    def save_replay(self, replay: ReplayRun) -> ReplayRun:
        """Persist and return a replay run."""
        self._ensure_schema()
        stored = replay.model_copy(update={"created_at": replay.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_replay_runs).where(aion_replay_runs.c.replay_id == stored.replay_id)
            )
            connection.execute(insert(aion_replay_runs).values(**stored.model_dump(mode="python")))
        return stored

    def get_replay(self, replay_id: str) -> ReplayRun | None:
        """Return a replay run by ID."""
        self._ensure_schema()
        statement = select(aion_replay_runs).where(aion_replay_runs.c.replay_id == replay_id)
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_replay(row) if row is not None else None

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        replay_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_snapshot(row: RowMapping) -> BrainSnapshot:
    return BrainSnapshot(
        snapshot_id=str(row["snapshot_id"]),
        trace_id=_optional_str(row["trace_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_string_list(row["owner_scope"]),
        snapshot_type=cast(SnapshotType, str(row["snapshot_type"])),
        state=dict(row["state"]),
        content_hash=str(row["content_hash"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
    )


def _row_to_replay(row: RowMapping) -> ReplayRun:
    return ReplayRun(
        replay_id=str(row["replay_id"]),
        source_trace_id=str(row["source_trace_id"]),
        replay_trace_id=_optional_str(row["replay_trace_id"]),
        mode=cast(ReplayMode, str(row["mode"])),
        status=cast(ReplayStatus, str(row["status"])),
        input_snapshot_id=_optional_str(row["input_snapshot_id"]),
        output_snapshot_id=_optional_str(row["output_snapshot_id"]),
        comparison=dict(row["comparison"]),
        drift_detected=bool(row["drift_detected"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError("Expected datetime-compatible value")


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)
