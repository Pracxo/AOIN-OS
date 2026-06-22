"""Persistent cognitive task repository."""

from datetime import UTC, datetime
from typing import Any, cast

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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.goals import LifecyclePriority, LifecycleRiskLevel
from aion_brain.contracts.tasks import (
    CognitiveTask,
    TaskLifecycleEvent,
    TaskRunMode,
    TaskRunRecord,
    TaskRunStatus,
    TaskStatus,
    TaskType,
)

task_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_cognitive_tasks = Table(
    "aion_cognitive_tasks",
    task_metadata,
    Column("task_id", Text, primary_key=True),
    Column("goal_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("plan_id", Text, nullable=True),
    Column("execution_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("task_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("priority", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("due_at", DateTime(timezone=True), nullable=True),
    Column("scheduled_for", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("cancelled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_cognitive_tasks_goal_id", "goal_id"),
    Index("ix_aion_cognitive_tasks_trace_id", "trace_id"),
    Index("ix_aion_cognitive_tasks_plan_id", "plan_id"),
    Index("ix_aion_cognitive_tasks_execution_id", "execution_id"),
    Index("ix_aion_cognitive_tasks_actor_id", "actor_id"),
    Index("ix_aion_cognitive_tasks_workspace_id", "workspace_id"),
    Index("ix_aion_cognitive_tasks_task_type", "task_type"),
    Index("ix_aion_cognitive_tasks_status", "status"),
    Index("ix_aion_cognitive_tasks_priority", "priority"),
    Index("ix_aion_cognitive_tasks_risk_level", "risk_level"),
    Index("ix_aion_cognitive_tasks_due_at", "due_at"),
    Index("ix_aion_cognitive_tasks_scheduled_for", "scheduled_for"),
    Index("ix_aion_cognitive_tasks_created_at", "created_at"),
)

aion_task_runs = Table(
    "aion_task_runs",
    task_metadata,
    Column("task_run_id", Text, primary_key=True),
    Column("task_id", Text, ForeignKey("aion_cognitive_tasks.task_id"), nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("execution_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("run_mode", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_task_runs_task_id", "task_id"),
    Index("ix_aion_task_runs_trace_id", "trace_id"),
    Index("ix_aion_task_runs_execution_id", "execution_id"),
    Index("ix_aion_task_runs_status", "status"),
    Index("ix_aion_task_runs_run_mode", "run_mode"),
    Index("ix_aion_task_runs_created_at", "created_at"),
)

aion_task_lifecycle_events = Table(
    "aion_task_lifecycle_events",
    task_metadata,
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


class TaskRepository:
    """Repository for cognitive tasks, runs, and lifecycle events."""

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

    def save_task(self, task: CognitiveTask) -> CognitiveTask:
        """Upsert a cognitive task."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = task.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = task.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_cognitive_tasks.c.task_id).where(
                    aion_cognitive_tasks.c.task_id == task.task_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_cognitive_tasks).values(**values))
            else:
                connection.execute(
                    update(aion_cognitive_tasks)
                    .where(aion_cognitive_tasks.c.task_id == task.task_id)
                    .values(**values)
                )
        return stored

    def get_task(self, task_id: str) -> CognitiveTask | None:
        """Return a task by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_cognitive_tasks).where(aion_cognitive_tasks.c.task_id == task_id)
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return _row_to_task(row)

    def list_tasks(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        goal_id: str | None = None,
        limit: int = 50,
    ) -> list[CognitiveTask]:
        """Return tasks filtered by scope and optional status or goal."""
        self._ensure_schema()
        statement = (
            select(aion_cognitive_tasks)
            .order_by(aion_cognitive_tasks.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_cognitive_tasks.c.status == status)
        if goal_id is not None:
            statement = statement.where(aion_cognitive_tasks.c.goal_id == goal_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [task for task in (_row_to_task(row) for row in rows) if _within_scope(task, scope)]

    def save_task_run(self, run: TaskRunRecord) -> TaskRunRecord:
        """Persist a task run record."""
        self._ensure_schema()
        stored = run.model_copy(update={"created_at": run.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(insert(aion_task_runs).values(**stored.model_dump(mode="python")))
        return stored

    def list_task_runs(self, task_id: str) -> list[TaskRunRecord]:
        """Return task run records for a task."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(aion_task_runs)
                    .where(aion_task_runs.c.task_id == task_id)
                    .order_by(aion_task_runs.c.created_at)
                )
                .mappings()
                .all()
            )
        return [_row_to_task_run(row) for row in rows]

    def save_lifecycle_event(self, event: TaskLifecycleEvent) -> TaskLifecycleEvent:
        """Persist a lifecycle event."""
        self._ensure_schema()
        stored = event.model_copy(update={"created_at": event.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_task_lifecycle_events).values(**stored.model_dump(mode="python"))
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        task_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_task(row: RowMapping) -> CognitiveTask:
    return CognitiveTask(
        task_id=str(row["task_id"]),
        goal_id=_optional_str(row["goal_id"]),
        trace_id=_optional_str(row["trace_id"]),
        plan_id=_optional_str(row["plan_id"]),
        execution_id=_optional_str(row["execution_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        title=str(row["title"]),
        description=str(row["description"]),
        task_type=cast(TaskType, str(row["task_type"])),
        status=cast(TaskStatus, str(row["status"])),
        priority=cast(LifecyclePriority, str(row["priority"])),
        risk_level=cast(LifecycleRiskLevel, str(row["risk_level"])),
        owner_scope=_str_list(row["owner_scope"]),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        constraints=_str_list(row["constraints"]),
        metadata=_dict(row["metadata"]),
        due_at=_optional_datetime(row["due_at"]),
        scheduled_for=_optional_datetime(row["scheduled_for"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        cancelled_at=_optional_datetime(row["cancelled_at"]),
    )


def _row_to_task_run(row: RowMapping) -> TaskRunRecord:
    return TaskRunRecord(
        task_run_id=str(row["task_run_id"]),
        task_id=str(row["task_id"]),
        trace_id=_optional_str(row["trace_id"]),
        execution_id=_optional_str(row["execution_id"]),
        status=cast(TaskRunStatus, str(row["status"])),
        run_mode=cast(TaskRunMode, str(row["run_mode"])),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _within_scope(task: CognitiveTask, scope: list[str]) -> bool:
    return not scope or any(item in task.owner_scope for item in scope)


def _str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


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
