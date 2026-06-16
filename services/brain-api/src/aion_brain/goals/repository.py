"""Persistent goal repository."""

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

from aion_brain.contracts.goals import (
    GoalRecord,
    GoalStatus,
    LifecyclePriority,
    LifecycleRiskLevel,
)
from aion_brain.contracts.tasks import LifecycleEventType, TaskLifecycleEvent

goal_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_goals = Table(
    "aion_goals",
    goal_metadata,
    Column("goal_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("priority", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("success_criteria", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("cancelled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_goals_trace_id", "trace_id"),
    Index("ix_aion_goals_actor_id", "actor_id"),
    Index("ix_aion_goals_workspace_id", "workspace_id"),
    Index("ix_aion_goals_status", "status"),
    Index("ix_aion_goals_priority", "priority"),
    Index("ix_aion_goals_risk_level", "risk_level"),
    Index("ix_aion_goals_created_at", "created_at"),
    Index("ix_aion_goals_updated_at", "updated_at"),
)

aion_goal_lifecycle_events = Table(
    "aion_task_lifecycle_events",
    goal_metadata,
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
    Index("ix_aion_task_lifecycle_events_goal_id", "goal_id"),
    Index("ix_aion_task_lifecycle_events_task_id", "task_id"),
    Index("ix_aion_task_lifecycle_events_trace_id", "trace_id"),
    Index("ix_aion_task_lifecycle_events_event_type", "event_type"),
    Index("ix_aion_task_lifecycle_events_from_status", "from_status"),
    Index("ix_aion_task_lifecycle_events_to_status", "to_status"),
    Index("ix_aion_task_lifecycle_events_created_at", "created_at"),
)


class GoalRepository:
    """Repository for goals and goal lifecycle events."""

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

    def save_goal(self, goal: GoalRecord) -> GoalRecord:
        """Upsert a goal record."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = goal.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = goal.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_goals.c.goal_id).where(aion_goals.c.goal_id == goal.goal_id)
            ).first()
            if existing is None:
                connection.execute(insert(aion_goals).values(**values))
            else:
                connection.execute(
                    update(aion_goals).where(aion_goals.c.goal_id == goal.goal_id).values(**values)
                )
        return stored

    def get_goal(self, goal_id: str) -> GoalRecord | None:
        """Return a goal by ID."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(aion_goals).where(aion_goals.c.goal_id == goal_id))
                .mappings()
                .first()
            )
        if row is None:
            return None
        return _row_to_goal(row)

    def list_goals(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[GoalRecord]:
        """Return goals filtered by scope and optional status."""
        self._ensure_schema()
        statement = select(aion_goals).order_by(aion_goals.c.created_at.desc()).limit(limit)
        if status is not None:
            statement = statement.where(aion_goals.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [goal for goal in (_row_to_goal(row) for row in rows) if _within_scope(goal, scope)]

    def save_lifecycle_event(self, event: TaskLifecycleEvent) -> TaskLifecycleEvent:
        """Persist a lifecycle event."""
        self._ensure_schema()
        stored = event.model_copy(update={"created_at": event.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_goal_lifecycle_events).values(**stored.model_dump(mode="python"))
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        goal_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_goal(row: RowMapping) -> GoalRecord:
    return GoalRecord(
        goal_id=str(row["goal_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        title=str(row["title"]),
        description=str(row["description"]),
        status=cast(GoalStatus, str(row["status"])),
        priority=cast(LifecyclePriority, str(row["priority"])),
        risk_level=cast(LifecycleRiskLevel, str(row["risk_level"])),
        owner_scope=_str_list(row["owner_scope"]),
        constraints=_str_list(row["constraints"]),
        success_criteria=_str_list(row["success_criteria"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        cancelled_at=_optional_datetime(row["cancelled_at"]),
    )


def _row_to_event(row: RowMapping) -> TaskLifecycleEvent:
    return TaskLifecycleEvent(
        lifecycle_event_id=str(row["lifecycle_event_id"]),
        task_id=_optional_str(row["task_id"]),
        goal_id=_optional_str(row["goal_id"]),
        trace_id=_optional_str(row["trace_id"]),
        event_type=cast(LifecycleEventType, str(row["event_type"])),
        from_status=_optional_str(row["from_status"]),
        to_status=_optional_str(row["to_status"]),
        reason=_optional_str(row["reason"]),
        payload=_dict(row["payload"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _within_scope(goal: GoalRecord, scope: list[str]) -> bool:
    return not scope or any(item in goal.owner_scope for item in scope)


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
