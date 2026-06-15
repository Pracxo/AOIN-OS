"""Cognitive task lifecycle contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.goals import LifecyclePriority, LifecycleRiskLevel

TaskStatus = Literal[
    "proposed",
    "queued",
    "running",
    "waiting_for_approval",
    "blocked_by_policy",
    "completed",
    "cancelled",
    "failed",
]
TaskType = Literal[
    "brain.think",
    "brain.plan",
    "brain.execute",
    "brain.retrieve",
    "brain.evaluate",
    "brain.learn",
    "capability.invoke",
    "generic",
]
TaskRunMode = Literal["dry_run", "controlled"]
TaskRunStatus = Literal[
    "started",
    "completed",
    "blocked_by_policy",
    "waiting_for_approval",
    "failed",
]
LifecycleEventType = Literal[
    "goal_created",
    "goal_transitioned",
    "task_created",
    "task_transitioned",
    "task_run_started",
    "task_run_completed",
    "task_run_blocked",
    "task_run_failed",
    "schedule_created",
    "schedule_updated",
]


class CognitiveTask(BaseModel):
    """Persistent generic cognitive task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    goal_id: str | None = None
    trace_id: str | None = None
    plan_id: str | None = None
    execution_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    task_type: TaskType
    status: TaskStatus
    priority: LifecyclePriority
    risk_level: LifecycleRiskLevel
    owner_scope: list[str] = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    due_at: datetime | None = None
    scheduled_for: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None

    @field_validator("title", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text fields."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class TaskCreateRequest(BaseModel):
    """Request to create a proposed cognitive task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str | None = None
    goal_id: str | None = None
    trace_id: str | None = None
    plan_id: str | None = None
    execution_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    task_type: TaskType = "generic"
    priority: LifecyclePriority = "normal"
    risk_level: LifecycleRiskLevel = "medium"
    owner_scope: list[str] = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    due_at: datetime | None = None
    scheduled_for: datetime | None = None

    @field_validator("title", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text fields."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class TaskTransitionRequest(BaseModel):
    """Request to transition a cognitive task."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    to_status: TaskStatus
    reason: str | None = None
    actor_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskRunRequest(BaseModel):
    """Request to run a cognitive task."""

    model_config = ConfigDict(extra="forbid")

    task_run_id: str | None = None
    task_id: str = Field(min_length=1)
    trace_id: str | None = None
    run_mode: TaskRunMode = "dry_run"
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskRunRecord(BaseModel):
    """Persistent record for one task run attempt."""

    model_config = ConfigDict(extra="forbid")

    task_run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    trace_id: str | None = None
    execution_id: str | None = None
    status: TaskRunStatus
    run_mode: TaskRunMode
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None


class TaskLifecycleEvent(BaseModel):
    """Goal, task, or schedule lifecycle event."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_event_id: str = Field(min_length=1)
    task_id: str | None = None
    goal_id: str | None = None
    trace_id: str | None = None
    event_type: LifecycleEventType
    from_status: str | None = None
    to_status: str | None = None
    reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
