"""Persistent schedule metadata repository."""

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
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.schedules import (
    ScheduleOwnerType,
    ScheduleRecord,
    ScheduleStatus,
    ScheduleType,
)
from aion_brain.contracts.tasks import TaskLifecycleEvent

schedule_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_schedules = Table(
    "aion_schedules",
    schedule_metadata,
    Column("schedule_id", Text, primary_key=True),
    Column("owner_type", Text, nullable=False),
    Column("owner_id", Text, nullable=False),
    Column("schedule_type", Text, nullable=False),
    Column("schedule_expression", Text, nullable=False),
    Column("timezone", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("next_run_at", DateTime(timezone=True), nullable=True),
    Column("last_run_at", DateTime(timezone=True), nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_schedules_owner_type", "owner_type"),
    Index("ix_aion_schedules_owner_id", "owner_id"),
    Index("ix_aion_schedules_schedule_type", "schedule_type"),
    Index("ix_aion_schedules_status", "status"),
    Index("ix_aion_schedules_next_run_at", "next_run_at"),
    Index("ix_aion_schedules_created_at", "created_at"),
)

aion_schedule_lifecycle_events = Table(
    "aion_task_lifecycle_events",
    schedule_metadata,
    Column("lifecycle_event_id", Text, primary_key=True),
    Column("task_id", Text, nullable=True),
    Column("goal_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("event_type", Text, nullable=False),
    Column("from_status", Text, nullable=True),
    Column("to_status", Text, nullable=True),
    Column("reason", Text, nullable=True),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_task_lifecycle_events_task_id", "task_id"),
    Index("ix_aion_task_lifecycle_events_goal_id", "goal_id"),
    Index("ix_aion_task_lifecycle_events_trace_id", "trace_id"),
    Index("ix_aion_task_lifecycle_events_event_type", "event_type"),
    Index("ix_aion_task_lifecycle_events_from_status", "from_status"),
    Index("ix_aion_task_lifecycle_events_to_status", "to_status"),
    Index("ix_aion_task_lifecycle_events_created_at", "created_at"),
)


class ScheduleRepository:
    """Repository for schedule metadata."""

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

    def save_schedule(self, schedule: ScheduleRecord) -> ScheduleRecord:
        """Upsert schedule metadata."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = schedule.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = schedule.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_schedules.c.schedule_id).where(
                    aion_schedules.c.schedule_id == schedule.schedule_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_schedules).values(**values))
            else:
                connection.execute(
                    update(aion_schedules)
                    .where(aion_schedules.c.schedule_id == schedule.schedule_id)
                    .values(**values)
                )
        return stored

    def get_schedule(self, schedule_id: str) -> ScheduleRecord | None:
        """Return schedule metadata by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_schedules).where(aion_schedules.c.schedule_id == schedule_id)
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return _row_to_schedule(row)

    def list_schedules(
        self,
        *,
        owner_type: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ScheduleRecord]:
        """Return schedule metadata records."""
        self._ensure_schema()
        statement = select(aion_schedules).order_by(aion_schedules.c.created_at.desc()).limit(limit)
        if owner_type is not None:
            statement = statement.where(aion_schedules.c.owner_type == owner_type)
        if owner_id is not None:
            statement = statement.where(aion_schedules.c.owner_id == owner_id)
        if status is not None:
            statement = statement.where(aion_schedules.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_schedule(row) for row in rows]

    def save_lifecycle_event(self, event: TaskLifecycleEvent) -> TaskLifecycleEvent:
        """Persist a schedule lifecycle event."""
        self._ensure_schema()
        stored = event.model_copy(update={"created_at": event.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_schedule_lifecycle_events).values(**stored.model_dump(mode="python"))
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        schedule_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_schedule(row: RowMapping) -> ScheduleRecord:
    return ScheduleRecord(
        schedule_id=str(row["schedule_id"]),
        owner_type=cast(ScheduleOwnerType, str(row["owner_type"])),
        owner_id=str(row["owner_id"]),
        schedule_type=cast(ScheduleType, str(row["schedule_type"])),
        schedule_expression=str(row["schedule_expression"]),
        timezone=str(row["timezone"]),
        status=cast(ScheduleStatus, str(row["status"])),
        next_run_at=_optional_datetime(row["next_run_at"]),
        last_run_at=_optional_datetime(row["last_run_at"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
