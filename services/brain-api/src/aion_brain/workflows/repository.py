"""Persistent durable workflow repository."""

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
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.workflows import (
    WorkflowActionType,
    WorkflowDefinition,
    WorkflowDefinitionStatus,
    WorkflowHeartbeat,
    WorkflowRetryPolicy,
    WorkflowRiskLevel,
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowStep,
    WorkflowStepRun,
    WorkflowStepRunStatus,
    WorkflowTriggerType,
    WorkflowWorkerRecord,
)

workflow_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_workflow_definitions = Table(
    "aion_workflow_definitions",
    workflow_metadata,
    Column("workflow_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("trigger_type", Text, nullable=False),
    Column("trigger_config", json_payload_type, nullable=False),
    Column("steps", json_payload_type, nullable=False),
    Column("retry_policy", json_payload_type, nullable=False),
    Column("timeout_seconds", Integer, nullable=True),
    Column("risk_level", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_workflow_definitions_name", "name"),
    Index("ix_aion_workflow_definitions_status", "status"),
    Index("ix_aion_workflow_definitions_trigger_type", "trigger_type"),
    Index("ix_aion_workflow_definitions_risk_level", "risk_level"),
    Index("ix_aion_workflow_definitions_created_by", "created_by"),
    Index("ix_aion_workflow_definitions_created_at", "created_at"),
)

aion_workflow_runs = Table(
    "aion_workflow_runs",
    workflow_metadata,
    Column("workflow_run_id", Text, primary_key=True),
    Column("workflow_id", Text, nullable=False),
    Column("trace_id", Text, nullable=True),
    Column("task_id", Text, nullable=True),
    Column("goal_id", Text, nullable=True),
    Column("execution_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("trigger_type", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("retry_count", Integer, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("next_retry_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_workflow_runs_workflow_id", "workflow_id"),
    Index("ix_aion_workflow_runs_trace_id", "trace_id"),
    Index("ix_aion_workflow_runs_task_id", "task_id"),
    Index("ix_aion_workflow_runs_goal_id", "goal_id"),
    Index("ix_aion_workflow_runs_execution_id", "execution_id"),
    Index("ix_aion_workflow_runs_actor_id", "actor_id"),
    Index("ix_aion_workflow_runs_workspace_id", "workspace_id"),
    Index("ix_aion_workflow_runs_status", "status"),
    Index("ix_aion_workflow_runs_trigger_type", "trigger_type"),
    Index("ix_aion_workflow_runs_next_retry_at", "next_retry_at"),
    Index("ix_aion_workflow_runs_created_at", "created_at"),
)

aion_workflow_step_runs = Table(
    "aion_workflow_step_runs",
    workflow_metadata,
    Column("workflow_step_run_id", Text, primary_key=True),
    Column(
        "workflow_run_id",
        Text,
        ForeignKey("aion_workflow_runs.workflow_run_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("step_id", Text, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("attempt", Integer, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_workflow_step_runs_run", "workflow_run_id"),
    Index("ix_aion_workflow_step_runs_step_id", "step_id"),
    Index("ix_aion_workflow_step_runs_action", "action_type"),
    Index("ix_aion_workflow_step_runs_status", "status"),
    Index("ix_aion_workflow_step_runs_attempt", "attempt"),
    Index("ix_aion_workflow_step_runs_created_at", "created_at"),
)

aion_workflow_heartbeats = Table(
    "aion_workflow_heartbeats",
    workflow_metadata,
    Column("heartbeat_id", Text, primary_key=True),
    Column("workflow_run_id", Text, nullable=True),
    Column("worker_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_workflow_heartbeats_run", "workflow_run_id"),
    Index("ix_aion_workflow_heartbeats_worker", "worker_id"),
    Index("ix_aion_workflow_heartbeats_status", "status"),
    Index("ix_aion_workflow_heartbeats_created_at", "created_at"),
)

aion_workflow_worker_records = Table(
    "aion_workflow_worker_records",
    workflow_metadata,
    Column("worker_id", Text, primary_key=True),
    Column("worker_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("last_heartbeat_at", DateTime(timezone=True), nullable=True),
    Column("capabilities", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("stopped_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_workflow_workers_type", "worker_type"),
    Index("ix_aion_workflow_workers_status", "status"),
    Index("ix_aion_workflow_workers_last_heartbeat", "last_heartbeat_at"),
    Index("ix_aion_workflow_workers_created_at", "created_at"),
)

aion_workflow_events = Table(
    "aion_workflow_events",
    workflow_metadata,
    Column("workflow_event_id", Text, primary_key=True),
    Column("workflow_id", Text, nullable=True),
    Column("workflow_run_id", Text, nullable=True),
    Column("step_run_id", Text, nullable=True),
    Column("event_type", Text, nullable=False),
    Column("from_status", Text, nullable=True),
    Column("to_status", Text, nullable=True),
    Column("reason", Text, nullable=True),
    Column("payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_workflow_events_workflow_id", "workflow_id"),
    Index("ix_aion_workflow_events_run", "workflow_run_id"),
    Index("ix_aion_workflow_events_step", "step_run_id"),
    Index("ix_aion_workflow_events_type", "event_type"),
    Index("ix_aion_workflow_events_from_status", "from_status"),
    Index("ix_aion_workflow_events_to_status", "to_status"),
    Index("ix_aion_workflow_events_created_at", "created_at"),
)


class WorkflowRepository:
    """Repository for durable workflow definitions, runs, workers, and events."""

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
            if database_url.startswith("sqlite"):
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(
                    database_url,
                    poolclass=QueuePool,
                    pool_pre_ping=True,
                )
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_workflow(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        """Upsert a workflow definition."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = workflow.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        values["steps"] = [step.model_dump(mode="json") for step in workflow.steps]
        values["retry_policy"] = workflow.retry_policy.model_dump(mode="json")
        stored = workflow.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_workflow_definitions.c.workflow_id).where(
                    aion_workflow_definitions.c.workflow_id == workflow.workflow_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_workflow_definitions).values(**values))
            else:
                connection.execute(
                    update(aion_workflow_definitions)
                    .where(aion_workflow_definitions.c.workflow_id == workflow.workflow_id)
                    .values(**values)
                )
        return stored

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        """Return one workflow definition."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_workflow_definitions).where(
                        aion_workflow_definitions.c.workflow_id == workflow_id
                    )
                )
                .mappings()
                .first()
            )
        return _definition_from_row(row) if row is not None else None

    def list_workflows(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkflowDefinition]:
        """List workflow definitions filtered by scope and status."""
        self._ensure_schema()
        statement = (
            select(aion_workflow_definitions)
            .order_by(aion_workflow_definitions.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            statement = statement.where(aion_workflow_definitions.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            workflow
            for workflow in (_definition_from_row(row) for row in rows)
            if _within_scope(workflow.owner_scope, scope)
        ]

    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        """Upsert a workflow run without duplicating embedded step rows."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = run.model_dump(mode="python", exclude={"step_runs"})
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = run.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_workflow_runs.c.workflow_run_id).where(
                    aion_workflow_runs.c.workflow_run_id == run.workflow_run_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_workflow_runs).values(**values))
            else:
                connection.execute(
                    update(aion_workflow_runs)
                    .where(aion_workflow_runs.c.workflow_run_id == run.workflow_run_id)
                    .values(**values)
                )
        return stored

    def get_run(self, workflow_run_id: str) -> WorkflowRun | None:
        """Return one workflow run with step runs."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_workflow_runs).where(
                        aion_workflow_runs.c.workflow_run_id == workflow_run_id
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        run = _run_from_row(row)
        return run.model_copy(update={"step_runs": self.list_step_runs(run.workflow_run_id)})

    def list_runs(
        self,
        *,
        workflow_id: str | None = None,
        status: str | None = None,
        scope: list[str] | None = None,
        limit: int = 50,
    ) -> list[WorkflowRun]:
        """List workflow runs."""
        self._ensure_schema()
        statement = (
            select(aion_workflow_runs).order_by(aion_workflow_runs.c.created_at.desc()).limit(limit)
        )
        if workflow_id is not None:
            statement = statement.where(aion_workflow_runs.c.workflow_id == workflow_id)
        if status is not None:
            statement = statement.where(aion_workflow_runs.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        runs = [_run_from_row(row) for row in rows]
        scoped = (
            runs if scope is None else [run for run in runs if _run_within_scope(run, scope, self)]
        )
        return [
            run.model_copy(update={"step_runs": self.list_step_runs(run.workflow_run_id)})
            for run in scoped
        ]

    def list_runnable_runs(self, *, limit: int, now: datetime) -> list[WorkflowRun]:
        """Return pending or due retry runs for explicit worker ticks."""
        self._ensure_schema()
        statement = (
            select(aion_workflow_runs)
            .where(
                (aion_workflow_runs.c.status == "pending")
                | (
                    (aion_workflow_runs.c.status == "retry_scheduled")
                    & (
                        (aion_workflow_runs.c.next_retry_at.is_(None))
                        | (aion_workflow_runs.c.next_retry_at <= now)
                    )
                )
            )
            .order_by(aion_workflow_runs.c.created_at)
            .limit(limit)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_run_from_row(row) for row in rows]

    def save_step_run(self, step_run: WorkflowStepRun) -> WorkflowStepRun:
        """Upsert a workflow step run."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = step_run.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = step_run.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_workflow_step_runs.c.workflow_step_run_id).where(
                    aion_workflow_step_runs.c.workflow_step_run_id == step_run.workflow_step_run_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_workflow_step_runs).values(**values))
            else:
                connection.execute(
                    update(aion_workflow_step_runs)
                    .where(
                        aion_workflow_step_runs.c.workflow_step_run_id
                        == step_run.workflow_step_run_id
                    )
                    .values(**values)
                )
        return stored

    def list_step_runs(self, workflow_run_id: str) -> list[WorkflowStepRun]:
        """Return step runs for a workflow run."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(aion_workflow_step_runs)
                    .where(aion_workflow_step_runs.c.workflow_run_id == workflow_run_id)
                    .order_by(aion_workflow_step_runs.c.created_at)
                )
                .mappings()
                .all()
            )
        return [_step_run_from_row(row) for row in rows]

    def save_heartbeat(self, heartbeat: WorkflowHeartbeat) -> WorkflowHeartbeat:
        """Persist a worker heartbeat."""
        self._ensure_schema()
        stored = heartbeat.model_copy(
            update={"created_at": heartbeat.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_workflow_heartbeats).values(**stored.model_dump(mode="python"))
            )
        return stored

    def save_worker(self, worker: WorkflowWorkerRecord) -> WorkflowWorkerRecord:
        """Upsert a worker record."""
        self._ensure_schema()
        now = datetime.now(UTC)
        values = worker.model_dump(mode="python")
        values["created_at"] = values["created_at"] or now
        values["updated_at"] = now
        stored = worker.model_copy(
            update={"created_at": values["created_at"], "updated_at": values["updated_at"]}
        )
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_workflow_worker_records.c.worker_id).where(
                    aion_workflow_worker_records.c.worker_id == worker.worker_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_workflow_worker_records).values(**values))
            else:
                connection.execute(
                    update(aion_workflow_worker_records)
                    .where(aion_workflow_worker_records.c.worker_id == worker.worker_id)
                    .values(**values)
                )
        return stored

    def save_event(
        self,
        *,
        workflow_event_id: str,
        workflow_id: str | None,
        workflow_run_id: str | None,
        step_run_id: str | None,
        event_type: str,
        from_status: str | None,
        to_status: str | None,
        reason: str | None,
        payload: dict[str, Any],
        created_at: datetime | None = None,
    ) -> None:
        """Persist a workflow lifecycle event."""
        self._ensure_schema()
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_workflow_events).values(
                    workflow_event_id=workflow_event_id,
                    workflow_id=workflow_id,
                    workflow_run_id=workflow_run_id,
                    step_run_id=step_run_id,
                    event_type=event_type,
                    from_status=from_status,
                    to_status=to_status,
                    reason=reason,
                    payload=payload,
                    created_at=created_at or datetime.now(UTC),
                )
            )

    def count_runs(self, status: str) -> int:
        """Count workflow runs by status."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(aion_workflow_runs.c.workflow_run_id).where(
                    aion_workflow_runs.c.status == status
                )
            ).all()
        return len(rows)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        workflow_metadata.create_all(self._engine)
        self._schema_ready = True


def _definition_from_row(row: RowMapping) -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id=str(row["workflow_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(WorkflowDefinitionStatus, str(row["status"])),
        owner_scope=_str_list(row["owner_scope"]),
        trigger_type=cast(WorkflowTriggerType, str(row["trigger_type"])),
        trigger_config=_dict(row["trigger_config"]),
        steps=[WorkflowStep(**item) for item in _dict_list(row["steps"])],
        retry_policy=WorkflowRetryPolicy(**_dict(row["retry_policy"])),
        timeout_seconds=_optional_int(row["timeout_seconds"]),
        risk_level=cast(WorkflowRiskLevel, str(row["risk_level"])),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _run_from_row(row: RowMapping) -> WorkflowRun:
    return WorkflowRun(
        workflow_run_id=str(row["workflow_run_id"]),
        workflow_id=str(row["workflow_id"]),
        trace_id=_optional_str(row["trace_id"]),
        task_id=_optional_str(row["task_id"]),
        goal_id=_optional_str(row["goal_id"]),
        execution_id=_optional_str(row["execution_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        status=cast(WorkflowRunStatus, str(row["status"])),
        trigger_type=cast(WorkflowTriggerType, str(row["trigger_type"])),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        retry_count=int(row["retry_count"]),
        step_runs=[],
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        next_retry_at=_optional_datetime(row["next_retry_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _step_run_from_row(row: RowMapping) -> WorkflowStepRun:
    return WorkflowStepRun(
        workflow_step_run_id=str(row["workflow_step_run_id"]),
        workflow_run_id=str(row["workflow_run_id"]),
        step_id=str(row["step_id"]),
        action_type=cast(WorkflowActionType, str(row["action_type"])),
        status=cast(WorkflowStepRunStatus, str(row["status"])),
        attempt=int(row["attempt"]),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _run_within_scope(
    run: WorkflowRun,
    scope: list[str],
    repository: WorkflowRepository,
) -> bool:
    workflow = repository.get_workflow(run.workflow_id)
    return workflow is not None and _within_scope(workflow.owner_scope, scope)


def _within_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return any(scope in owner_scope for scope in requested_scope)


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
