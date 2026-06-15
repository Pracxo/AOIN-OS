"""Persistent execution repository."""

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
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.execution import (
    ApprovalCheckpoint,
    ApprovalStatus,
    CapabilityInvocationRecord,
    CapabilityInvocationStatus,
    ExecutionRun,
    ExecutionStatus,
    ExecutionStepRun,
    ExecutionStepStatus,
)
from aion_brain.execution.state_machine import require_valid_execution_transition

execution_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_execution_runs = Table(
    "aion_execution_runs",
    execution_metadata,
    Column("execution_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("plan_id", Text, nullable=False),
    Column("intent_id", Text, nullable=True),
    Column("context_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("requested_by", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_execution_runs_trace_id", "trace_id"),
    Index("ix_aion_execution_runs_plan_id", "plan_id"),
    Index("ix_aion_execution_runs_intent_id", "intent_id"),
    Index("ix_aion_execution_runs_context_id", "context_id"),
    Index("ix_aion_execution_runs_status", "status"),
    Index("ix_aion_execution_runs_workspace_id", "workspace_id"),
    Index("ix_aion_execution_runs_created_at", "created_at"),
)

aion_execution_steps = Table(
    "aion_execution_steps",
    execution_metadata,
    Column("step_run_id", Text, primary_key=True),
    Column("execution_id", Text, ForeignKey("aion_execution_runs.execution_id"), nullable=False),
    Column("plan_id", Text, nullable=False),
    Column("step_id", Text, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("capability_required", Text, nullable=True),
    Column("risk_level", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("attempt", Integer, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("error", json_payload_type, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_execution_steps_execution_id", "execution_id"),
    Index("ix_aion_execution_steps_plan_id", "plan_id"),
    Index("ix_aion_execution_steps_step_id", "step_id"),
    Index("ix_aion_execution_steps_action_type", "action_type"),
    Index("ix_aion_execution_steps_capability_required", "capability_required"),
    Index("ix_aion_execution_steps_risk_level", "risk_level"),
    Index("ix_aion_execution_steps_status", "status"),
    Index("ix_aion_execution_steps_created_at", "created_at"),
)

aion_approval_checkpoints = Table(
    "aion_approval_checkpoints",
    execution_metadata,
    Column("approval_id", Text, primary_key=True),
    Column("execution_id", Text, nullable=False),
    Column("step_run_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("reason", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("requested_by", Text, nullable=True),
    Column("approved_by", Text, nullable=True),
    Column("approval_payload", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_approval_checkpoints_execution_id", "execution_id"),
    Index("ix_aion_approval_checkpoints_step_run_id", "step_run_id"),
    Index("ix_aion_approval_checkpoints_trace_id", "trace_id"),
    Index("ix_aion_approval_checkpoints_risk_level", "risk_level"),
    Index("ix_aion_approval_checkpoints_status", "status"),
    Index("ix_aion_approval_checkpoints_created_at", "created_at"),
)

aion_capability_invocation_records = Table(
    "aion_capability_invocation_records",
    execution_metadata,
    Column("invocation_id", Text, primary_key=True),
    Column("execution_id", Text, nullable=True),
    Column("step_run_id", Text, nullable=True),
    Column("trace_id", Text, nullable=True),
    Column("capability_id", Text, nullable=False),
    Column("input", json_payload_type, nullable=False),
    Column("output", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("policy_decision_id", Text, nullable=True),
    Column("latency_ms", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_capability_invocation_records_execution_id", "execution_id"),
    Index("ix_aion_capability_invocation_records_step_run_id", "step_run_id"),
    Index("ix_aion_capability_invocation_records_trace_id", "trace_id"),
    Index("ix_aion_capability_invocation_records_capability_id", "capability_id"),
    Index("ix_aion_capability_invocation_records_status", "status"),
    Index("ix_aion_capability_invocation_records_created_at", "created_at"),
)


class ExecutionRepository:
    """Repository for execution runs and related records."""

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

    def save_execution(self, run: ExecutionRun) -> ExecutionRun:
        """Upsert an execution run."""
        self._ensure_schema()
        values = _run_values(run)
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_execution_runs.c.execution_id).where(
                    aion_execution_runs.c.execution_id == run.execution_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_execution_runs).values(**values))
            else:
                connection.execute(
                    update(aion_execution_runs)
                    .where(aion_execution_runs.c.execution_id == run.execution_id)
                    .values(**values)
                )
        return run

    def save_step(self, step: ExecutionStepRun) -> ExecutionStepRun:
        """Upsert an execution step run."""
        self._ensure_schema()
        values = {**step.model_dump(mode="python"), "updated_at": datetime.now(UTC)}
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_execution_steps.c.step_run_id).where(
                    aion_execution_steps.c.step_run_id == step.step_run_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_execution_steps).values(**values))
            else:
                connection.execute(
                    update(aion_execution_steps)
                    .where(aion_execution_steps.c.step_run_id == step.step_run_id)
                    .values(**values)
                )
        return step

    def save_approval(self, approval: ApprovalCheckpoint) -> ApprovalCheckpoint:
        """Upsert an approval checkpoint."""
        self._ensure_schema()
        values = approval.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_approval_checkpoints.c.approval_id).where(
                    aion_approval_checkpoints.c.approval_id == approval.approval_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_approval_checkpoints).values(**values))
            else:
                connection.execute(
                    update(aion_approval_checkpoints)
                    .where(aion_approval_checkpoints.c.approval_id == approval.approval_id)
                    .values(**values)
                )
        return approval

    def save_capability_invocation(
        self,
        record: CapabilityInvocationRecord,
    ) -> CapabilityInvocationRecord:
        """Upsert a capability invocation record."""
        self._ensure_schema()
        values = record.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_capability_invocation_records.c.invocation_id).where(
                    aion_capability_invocation_records.c.invocation_id == record.invocation_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_capability_invocation_records).values(**values))
            else:
                connection.execute(
                    update(aion_capability_invocation_records)
                    .where(
                        aion_capability_invocation_records.c.invocation_id
                        == record.invocation_id
                    )
                    .values(**values)
                )
        return record

    def get_execution(self, execution_id: str) -> ExecutionRun | None:
        """Return an execution run with child records."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_execution_runs).where(
                    aion_execution_runs.c.execution_id == execution_id
                )
            ).mappings().first()
        if row is None:
            return None
        return _row_to_run(
            row,
            self.list_steps(execution_id),
            self.list_approvals(execution_id),
            self.list_capability_invocations(execution_id),
        )

    def list_steps(self, execution_id: str) -> list[ExecutionStepRun]:
        """Return execution steps for a run."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(aion_execution_steps)
                .where(aion_execution_steps.c.execution_id == execution_id)
                .order_by(aion_execution_steps.c.created_at)
            ).mappings().all()
        return [_row_to_step(row) for row in rows]

    def list_approvals(self, execution_id: str) -> list[ApprovalCheckpoint]:
        """Return approval checkpoints for a run."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(aion_approval_checkpoints)
                .where(aion_approval_checkpoints.c.execution_id == execution_id)
                .order_by(aion_approval_checkpoints.c.created_at)
            ).mappings().all()
        return [_row_to_approval(row) for row in rows]

    def list_capability_invocations(self, execution_id: str) -> list[CapabilityInvocationRecord]:
        """Return capability invocation records for a run."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(aion_capability_invocation_records)
                .where(aion_capability_invocation_records.c.execution_id == execution_id)
                .order_by(aion_capability_invocation_records.c.created_at)
            ).mappings().all()
        return [_row_to_invocation(row) for row in rows]

    def get_approval(self, approval_id: str) -> ApprovalCheckpoint | None:
        """Return an approval checkpoint."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_approval_checkpoints).where(
                    aion_approval_checkpoints.c.approval_id == approval_id
                )
            ).mappings().first()
        if row is None:
            return None
        return _row_to_approval(row)

    def cancel_execution(self, execution_id: str, *, reason: str) -> ExecutionRun | None:
        """Cancel a running or waiting execution."""
        run = self.get_execution(execution_id)
        if run is None:
            return None
        if run.status in {"completed", "cancelled"}:
            return run
        require_valid_execution_transition(run.status, "cancelled")
        now = datetime.now(UTC)
        updated = run.model_copy(
            update={
                "status": "cancelled",
                "error": {"reason": reason},
                "completed_at": now,
                "updated_at": now,
            }
        )
        return self.save_execution(updated)

    def resolve_approval(
        self,
        approval_id: str,
        *,
        approved: bool,
        approved_by: str,
        reason: str,
    ) -> ApprovalCheckpoint | None:
        """Resolve a pending approval checkpoint."""
        approval = self.get_approval(approval_id)
        if approval is None:
            return None
        if approval.status != "pending":
            return approval
        resolved = approval.model_copy(
            update={
                "status": "approved" if approved else "denied",
                "approved_by": approved_by,
                "approval_payload": {
                    **approval.approval_payload,
                    "resolution_reason": reason,
                },
                "resolved_at": datetime.now(UTC),
            }
        )
        return self.save_approval(resolved)

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        execution_metadata.create_all(self._engine)
        self._schema_ready = True


def _run_values(run: ExecutionRun) -> dict[str, Any]:
    dumped = run.model_dump(mode="python")
    dumped.pop("steps")
    dumped.pop("approvals")
    dumped.pop("capability_invocations")
    if dumped["updated_at"] is None:
        dumped["updated_at"] = datetime.now(UTC)
    return dumped


def _row_to_run(
    row: RowMapping,
    steps: list[ExecutionStepRun],
    approvals: list[ApprovalCheckpoint],
    invocations: list[CapabilityInvocationRecord],
) -> ExecutionRun:
    return ExecutionRun(
        execution_id=str(row["execution_id"]),
        trace_id=_optional_str(row["trace_id"]),
        plan_id=str(row["plan_id"]),
        intent_id=_optional_str(row["intent_id"]),
        context_id=_optional_str(row["context_id"]),
        status=cast(ExecutionStatus, str(row["status"])),
        requested_by=_optional_str(row["requested_by"]),
        workspace_id=_optional_str(row["workspace_id"]),
        steps=steps,
        approvals=approvals,
        capability_invocations=invocations,
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        created_at=_coerce_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _row_to_step(row: RowMapping) -> ExecutionStepRun:
    return ExecutionStepRun(
        step_run_id=str(row["step_run_id"]),
        execution_id=str(row["execution_id"]),
        plan_id=str(row["plan_id"]),
        step_id=str(row["step_id"]),
        action_type=str(row["action_type"]),
        capability_required=_optional_str(row["capability_required"]),
        risk_level=str(row["risk_level"]),
        status=cast(ExecutionStepStatus, str(row["status"])),
        attempt=int(row["attempt"]),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        error=_dict(row["error"]),
        policy_decision_id=_optional_str(row["policy_decision_id"]),
        started_at=_optional_datetime(row["started_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
        created_at=_coerce_datetime(row["created_at"]),
    )


def _row_to_approval(row: RowMapping) -> ApprovalCheckpoint:
    return ApprovalCheckpoint(
        approval_id=str(row["approval_id"]),
        execution_id=str(row["execution_id"]),
        step_run_id=_optional_str(row["step_run_id"]),
        trace_id=_optional_str(row["trace_id"]),
        reason=str(row["reason"]),
        risk_level=str(row["risk_level"]),
        status=cast(ApprovalStatus, str(row["status"])),
        requested_by=_optional_str(row["requested_by"]),
        approved_by=_optional_str(row["approved_by"]),
        approval_payload=_dict(row["approval_payload"]),
        created_at=_coerce_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _row_to_invocation(row: RowMapping) -> CapabilityInvocationRecord:
    return CapabilityInvocationRecord(
        invocation_id=str(row["invocation_id"]),
        execution_id=_optional_str(row["execution_id"]),
        step_run_id=_optional_str(row["step_run_id"]),
        trace_id=_optional_str(row["trace_id"]),
        capability_id=str(row["capability_id"]),
        input=_dict(row["input"]),
        output=_dict(row["output"]),
        status=cast(CapabilityInvocationStatus, str(row["status"])),
        policy_decision_id=_optional_str(row["policy_decision_id"]),
        latency_ms=_optional_int(row["latency_ms"]),
        created_at=_coerce_datetime(row["created_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
