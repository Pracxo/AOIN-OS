"""Alert contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.notifications import NotificationSeverity

AlertType = Literal[
    "blocked_action",
    "pending_approval",
    "failed_run",
    "stalled_run",
    "timeout",
    "failed_security_check",
    "failed_audit_verification",
    "failed_grounding",
    "prompt_injection",
    "blocked_model_output",
    "captured_tool_intent",
    "failed_backup",
    "failed_release",
    "failed_freeze",
    "high_risk_learning_pattern",
    "contradiction",
    "operator_action",
    "generic",
]
AlertStatus = Literal["open", "acknowledged", "resolved", "dismissed", "archived", "deleted"]


def _validate_scope(value: list[str]) -> list[str]:
    if not value:
        raise ValueError("owner_scope cannot be empty")
    return value


class AlertRecord(BaseModel):
    """Generic local alert record."""

    model_config = ConfigDict(extra="forbid")

    alert_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    alert_type: AlertType
    status: AlertStatus
    severity: NotificationSeverity
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    owner_scope: list[str]
    notification_ids: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("description")
    @classmethod
    def description_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "alert description")
        return value

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class AlertCreateRequest(BaseModel):
    """Request to create a local alert."""

    model_config = ConfigDict(extra="forbid")

    alert_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    alert_type: AlertType
    severity: NotificationSeverity
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    owner_scope: list[str]
    blocker_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)


class AlertQuery(BaseModel):
    """Alert query contract."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str]
    trace_id: str | None = None
    alert_type: str | None = None
    status: str | None = None
    severity: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)

    @field_validator("scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)


__all__ = [
    "AlertCreateRequest",
    "AlertQuery",
    "AlertRecord",
    "AlertStatus",
    "AlertType",
]
