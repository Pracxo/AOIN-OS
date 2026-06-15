"""Goal lifecycle contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

GoalStatus = Literal["proposed", "active", "paused", "completed", "cancelled", "failed"]
LifecyclePriority = Literal["low", "normal", "high", "urgent"]
LifecycleRiskLevel = Literal["low", "medium", "high", "critical"]


class GoalRecord(BaseModel):
    """Persistent generic goal record."""

    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: GoalStatus
    priority: LifecyclePriority
    risk_level: LifecycleRiskLevel
    owner_scope: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None

    @field_validator("title", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text fields."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class GoalCreateRequest(BaseModel):
    """Request to create a proposed goal."""

    model_config = ConfigDict(extra="forbid")

    goal_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: LifecyclePriority = "normal"
    risk_level: LifecycleRiskLevel = "medium"
    owner_scope: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text fields."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class GoalTransitionRequest(BaseModel):
    """Request to transition a goal lifecycle status."""

    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(min_length=1)
    to_status: GoalStatus
    reason: str | None = None
    actor_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
