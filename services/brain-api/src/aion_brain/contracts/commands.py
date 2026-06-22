"""Command bus contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CommandType = Literal[
    "brain.think",
    "brain.plan",
    "brain.execute",
    "event.dispatch",
    "workflow.run",
    "task.run",
    "cycle.run",
    "memory.governance",
    "capability.invoke",
    "model.complete",
    "noop",
    "generic",
]
CommandTargetType = Literal[
    "brain",
    "event",
    "workflow",
    "task",
    "cycle",
    "memory",
    "capability",
    "model",
    "module",
    "trace",
    "noop",
]
CommandMode = Literal["dry_run", "controlled"]
CommandStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "waiting_for_approval",
    "duplicate",
    "cancelled",
]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "password",
    "private_key",
    "secret",
    "token",
}
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "hr",
    "procurement",
}


class BrainCommand(BaseModel):
    """Persistent command record for retry-safe Brain operations."""

    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    command_type: CommandType
    target_type: CommandTargetType
    target_id: str | None = None
    mode: CommandMode
    status: CommandStatus
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("command_id", "command_type", "target_type", "mode", "status")
    @classmethod
    def values_must_be_generic(cls, value: str) -> str:
        """Reject blank or vertical identifiers."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms(value)
        return value

    @field_validator("target_id")
    @classmethod
    def target_id_must_be_generic(cls, value: str | None) -> str | None:
        """Reject vertical target identifiers."""
        if value is not None:
            _reject_domain_terms(value)
        return value

    @field_validator("payload", "result", "error")
    @classmethod
    def payloads_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like payload keys."""
        _reject_secret_like_keys(value)
        return value


class CommandDispatchRequest(BaseModel):
    """Request to dispatch one Brain command."""

    model_config = ConfigDict(extra="forbid")

    command_id: str | None = None
    trace_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    command_type: CommandType
    target_type: CommandTargetType
    target_id: str | None = None
    mode: CommandMode = "dry_run"
    payload: dict[str, Any] = Field(default_factory=dict)
    approval_present: bool = False
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and vertical payloads."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class CommandDispatchResult(BaseModel):
    """Result of one command dispatch attempt."""

    model_config = ConfigDict(extra="forbid")

    command: BrainCommand
    duplicate: bool
    idempotency_key: str | None
    outbox_ids: list[str] = Field(default_factory=list)
    message: str
    created_at: datetime


def has_secret_like_key(value: object) -> bool:
    """Return whether a nested payload contains secret-like keys."""
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _SECRET_KEY_PARTS:
                return True
            if has_secret_like_key(nested):
                return True
    if isinstance(value, list):
        return any(has_secret_like_key(item) for item in value)
    return False


def _reject_secret_like_keys(value: object) -> None:
    if has_secret_like_key(value):
        raise ValueError("payload must not contain secret-like keys")


def _reject_domain_terms(value: object) -> None:
    text = str(value).lower()
    if any(term in text for term in _BANNED_DOMAIN_TERMS):
        raise ValueError("command contracts must remain domain-neutral")
