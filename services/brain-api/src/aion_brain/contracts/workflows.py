"""Durable workflow contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WorkflowActionType = Literal[
    "brain.think",
    "brain.plan",
    "brain.execute",
    "brain.retrieve",
    "brain.evaluate",
    "brain.learn",
    "task.run",
    "capability.invoke",
    "wait",
    "noop",
    "generic",
]
WorkflowRiskLevel = Literal["low", "medium", "high", "critical"]
WorkflowDefinitionStatus = Literal["draft", "active", "disabled", "archived"]
WorkflowTriggerType = Literal["manual", "schedule", "event", "task", "goal"]
WorkflowRunMode = Literal["dry_run", "controlled"]
WorkflowRunStatus = Literal[
    "pending",
    "running",
    "waiting_for_approval",
    "paused",
    "completed",
    "failed",
    "cancelled",
    "blocked_by_policy",
    "retry_scheduled",
]
WorkflowStepRunStatus = Literal[
    "pending",
    "running",
    "completed",
    "skipped",
    "failed",
    "blocked_by_policy",
    "waiting_for_approval",
]
WorkflowWorkerType = Literal["local_scheduler", "local_workflow", "temporal"]
WorkflowWorkerStatus = Literal["starting", "running", "idle", "stopped", "failed"]


class WorkflowStep(BaseModel):
    """A generic durable workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    action_type: WorkflowActionType
    description: str = Field(min_length=1)
    capability_required: str | None = None
    input_template: dict[str, Any] = Field(default_factory=dict)
    expected_output: dict[str, Any] = Field(default_factory=dict)
    risk_level: WorkflowRiskLevel
    timeout_seconds: int | None = Field(default=None, gt=0)
    retryable: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("step_id", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank identifiers and descriptions."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class WorkflowRetryPolicy(BaseModel):
    """Retry controls for a workflow run."""

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_seconds: int = Field(default=30, ge=0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    max_backoff_seconds: int = Field(default=3600)
    retry_on_statuses: list[str] = Field(default_factory=lambda: ["failed"])

    @model_validator(mode="after")
    def max_backoff_must_cover_initial_backoff(self) -> "WorkflowRetryPolicy":
        """Ensure retry backoff cannot shrink below the base backoff."""
        if self.max_backoff_seconds < self.backoff_seconds:
            raise ValueError("max_backoff_seconds must be >= backoff_seconds")
        return self


class WorkflowDefinition(BaseModel):
    """Persistent durable workflow definition."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: WorkflowDefinitionStatus
    owner_scope: list[str] = Field(min_length=1)
    trigger_type: WorkflowTriggerType
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    steps: list[WorkflowStep] = Field(min_length=1)
    retry_policy: WorkflowRetryPolicy = Field(default_factory=WorkflowRetryPolicy)
    timeout_seconds: int | None = Field(default=None, gt=0)
    risk_level: WorkflowRiskLevel
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class WorkflowCreateRequest(BaseModel):
    """Request to create a durable workflow definition."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    trigger_type: WorkflowTriggerType = "manual"
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    steps: list[WorkflowStep] = Field(min_length=1)
    retry_policy: WorkflowRetryPolicy = Field(default_factory=WorkflowRetryPolicy)
    timeout_seconds: int | None = Field(default=None, gt=0)
    risk_level: WorkflowRiskLevel = "medium"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    activate: bool = False


class WorkflowRunRequest(BaseModel):
    """Request to start or dry-run a durable workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow_run_id: str | None = None
    workflow_id: str = Field(min_length=1)
    trace_id: str | None = None
    task_id: str | None = None
    goal_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: WorkflowRunMode = "dry_run"
    input: dict[str, Any] = Field(default_factory=dict)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowStepRun(BaseModel):
    """Persistent state of one workflow step attempt."""

    model_config = ConfigDict(extra="forbid")

    workflow_step_run_id: str = Field(min_length=1)
    workflow_run_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    action_type: WorkflowActionType
    status: WorkflowStepRunStatus
    attempt: int = Field(ge=1)
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowRun(BaseModel):
    """Persistent durable workflow run."""

    model_config = ConfigDict(extra="forbid")

    workflow_run_id: str = Field(min_length=1)
    workflow_id: str = Field(min_length=1)
    trace_id: str | None = None
    task_id: str | None = None
    goal_id: str | None = None
    execution_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: WorkflowRunStatus
    trigger_type: WorkflowTriggerType
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    retry_count: int = Field(ge=0)
    step_runs: list[WorkflowStepRun] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    next_retry_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowTransitionRequest(BaseModel):
    """Request to transition a workflow run."""

    model_config = ConfigDict(extra="forbid")

    workflow_run_id: str = Field(min_length=1)
    to_status: WorkflowRunStatus
    reason: str | None = None
    actor_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowHeartbeat(BaseModel):
    """Worker heartbeat for a workflow run or scheduler tick."""

    model_config = ConfigDict(extra="forbid")

    heartbeat_id: str = Field(min_length=1)
    workflow_run_id: str | None = None
    worker_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class WorkflowWorkerRecord(BaseModel):
    """Persistent local workflow worker status."""

    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1)
    worker_type: WorkflowWorkerType
    status: WorkflowWorkerStatus
    last_heartbeat_at: datetime | None = None
    capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowEngineStatus(BaseModel):
    """Public status for the active workflow engine."""

    model_config = ConfigDict(extra="forbid")

    engine_name: str
    active_adapter: str
    temporal_available: bool
    temporal_enabled: bool
    local_worker_enabled: bool
    pending_runs: int
    running_runs: int
    failed_runs: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class TemporalAdapterStatus(BaseModel):
    """Public status for the optional Temporal adapter boundary."""

    model_config = ConfigDict(extra="forbid")

    adapter_name: str
    enabled: bool
    package_available: bool
    endpoint_ref: str | None
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
