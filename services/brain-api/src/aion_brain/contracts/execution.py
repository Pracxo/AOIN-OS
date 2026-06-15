"""Execution contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aion_brain.contracts.planning import PlanGraph

ExecutionMode = Literal["dry_run", "controlled"]
ExecutionStatus = Literal[
    "pending",
    "running",
    "completed",
    "blocked_by_policy",
    "waiting_for_approval",
    "failed",
    "cancelled",
]
ExecutionStepStatus = Literal[
    "pending",
    "running",
    "completed",
    "blocked_by_policy",
    "waiting_for_approval",
    "skipped",
    "failed",
]
ApprovalStatus = Literal["pending", "approved", "denied", "expired"]
CapabilityInvocationStatus = Literal[
    "not_implemented",
    "completed",
    "dry_run",
    "blocked_by_policy",
    "capability_not_found",
    "runtime_not_found",
    "runtime_unhealthy",
    "failed",
]


class ExecutionRequest(BaseModel):
    """Request to execute a plan through the controlled state machine."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str = Field(min_length=1)
    trace_id: str | None
    plan: PlanGraph
    requested_by: str | None
    workspace_id: str | None
    mode: ExecutionMode = "dry_run"
    approval_present: bool = False
    max_steps: int = Field(default=50, ge=1, le=100)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_plan_steps(self) -> "ExecutionRequest":
        """Execution requires at least one plan step."""
        if not self.plan.steps:
            raise ValueError("plan.steps cannot be empty")
        return self


class ExecutionStepRun(BaseModel):
    """State of a single plan step during execution."""

    model_config = ConfigDict(extra="forbid")

    step_run_id: str
    execution_id: str
    plan_id: str
    step_id: str
    action_type: str
    capability_required: str | None
    risk_level: str
    status: ExecutionStepStatus
    attempt: int
    input: dict[str, Any]
    output: dict[str, Any]
    error: dict[str, Any]
    policy_decision_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ApprovalCheckpoint(BaseModel):
    """Human or higher-authority approval checkpoint."""

    model_config = ConfigDict(extra="forbid")

    approval_id: str
    execution_id: str
    step_run_id: str | None
    trace_id: str | None
    reason: str
    risk_level: str
    status: ApprovalStatus
    requested_by: str | None
    approved_by: str | None
    approval_payload: dict[str, Any]
    created_at: datetime
    resolved_at: datetime | None


class CapabilityInvocationRecord(BaseModel):
    """Provider-neutral capability invocation ledger record."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str
    execution_id: str | None
    step_run_id: str | None
    trace_id: str | None
    capability_id: str
    input: dict[str, Any]
    output: dict[str, Any]
    status: CapabilityInvocationStatus
    policy_decision_id: str | None
    latency_ms: int | None = Field(default=None, ge=0)
    created_at: datetime


class ExecutionRun(BaseModel):
    """Auditable execution run for a plan."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str
    trace_id: str | None
    plan_id: str
    intent_id: str | None
    context_id: str | None
    status: ExecutionStatus
    requested_by: str | None
    workspace_id: str | None
    steps: list[ExecutionStepRun]
    approvals: list[ApprovalCheckpoint]
    capability_invocations: list[CapabilityInvocationRecord]
    input: dict[str, Any]
    output: dict[str, Any]
    error: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
