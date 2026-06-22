"""Approval control plane contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ApprovalStatus = Literal["pending", "approved", "denied", "expired", "cancelled"]
ApprovalPriority = Literal["low", "normal", "high", "urgent"]
ApprovalDecisionValue = Literal["approve", "deny", "cancel"]
ApprovalLifecycleEventType = Literal[
    "approval_created",
    "approval_assigned",
    "approval_approved",
    "approval_denied",
    "approval_cancelled",
    "approval_expired",
]

_SECRET_KEYS = {"api_key", "apikey", "secret", "token", "password", "private_key"}


class ApprovalRequest(BaseModel):
    """Persistent human review request."""

    model_config = ConfigDict(extra="forbid")

    approval_request_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    requested_by: str | None = None
    assigned_to: str | None = None
    action_type: str
    resource_type: str
    resource_id: str | None = None
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_assessment_id: str | None = None
    guardrail_decision_id: str | None = None
    status: ApprovalStatus
    priority: ApprovalPriority
    approval_scope: list[str] = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("title", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("payload")
    @classmethod
    def no_secret_like_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like approval payloads."""
        if _has_secret_like_key(value):
            raise ValueError("payload must not contain secret-like keys")
        return value


class ApprovalCreateRequest(BaseModel):
    """Request to create a human approval request."""

    model_config = ConfigDict(extra="forbid")

    approval_request_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    requested_by: str | None = None
    assigned_to: str | None = None
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_assessment_id: str | None = None
    guardrail_decision_id: str | None = None
    priority: ApprovalPriority = "normal"
    approval_scope: list[str] = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload", "metadata")
    @classmethod
    def no_secret_like_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys."""
        if _has_secret_like_key(value):
            raise ValueError("payload must not contain secret-like keys")
        return value


class ApprovalDecisionRequest(BaseModel):
    """Request to resolve a pending approval request."""

    model_config = ConfigDict(extra="forbid")

    approval_request_id: str = Field(min_length=1)
    decided_by: str | None = None
    decision: ApprovalDecisionValue
    reason: str = Field(min_length=1)
    decision_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Reject blank reasons."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value


class ApprovalDecision(BaseModel):
    """Persistent human approval decision."""

    model_config = ConfigDict(extra="forbid")

    approval_decision_id: str
    approval_request_id: str
    trace_id: str | None = None
    decided_by: str | None = None
    decision: ApprovalDecisionValue
    reason: str
    decision_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ApprovalInboxQuery(BaseModel):
    """Query for approval inbox records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    status: ApprovalStatus | None = "pending"
    priority: ApprovalPriority | None = None
    action_type: str | None = None
    resource_type: str | None = None
    limit: int = Field(default=50, ge=1, le=100)


class ApprovalLifecycleEvent(BaseModel):
    """Approval request lifecycle event."""

    model_config = ConfigDict(extra="forbid")

    approval_event_id: str
    approval_request_id: str
    trace_id: str | None = None
    event_type: ApprovalLifecycleEventType
    from_status: str | None = None
    to_status: str | None = None
    actor_id: str | None = None
    reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


def _has_secret_like_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower().replace("-", "_") in _SECRET_KEYS:
                return True
            if _has_secret_like_key(nested):
                return True
    if isinstance(value, list):
        return any(_has_secret_like_key(item) for item in value)
    return False
