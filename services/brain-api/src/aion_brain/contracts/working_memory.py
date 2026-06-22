"""Working memory contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

WorkingMemorySlotType = Literal[
    "active_goal",
    "active_task",
    "recent_event",
    "retrieved_context",
    "evidence_ref",
    "reasoning_note",
    "plan_note",
    "execution_note",
    "approval_note",
    "skill_ref",
    "user_preference",
    "system_constraint",
    "scratchpad",
]

WorkingMemorySourceType = Literal[
    "event",
    "goal",
    "task",
    "workflow",
    "memory",
    "evidence",
    "graph",
    "retrieval",
    "reasoning",
    "plan",
    "execution",
    "approval",
    "skill",
    "policy",
    "trace",
    "user_input",
    "system",
]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
    "authorization",
}
_CHAIN_OF_THOUGHT_KEY_PARTS = {
    "chain_of_thought",
    "chain-of-thought",
    "cot",
    "hidden_reasoning",
    "raw_reasoning",
}


class WorkingMemorySlot(BaseModel):
    """Short-lived cognitive state selected for focus."""

    model_config = ConfigDict(extra="forbid")

    slot_id: str = Field(min_length=1)
    focus_session_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    slot_type: WorkingMemorySlotType
    source_type: WorkingMemorySourceType
    source_id: str | None = None
    content: dict[str, Any]
    summary: str = Field(min_length=1)
    priority: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    ttl_seconds: int | None = Field(default=None, gt=0)
    expires_at: datetime | None = None
    pinned: bool
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("summary")
    @classmethod
    def summary_cannot_be_blank(cls, value: str) -> str:
        """Reject blank slot summaries."""
        if not value.strip():
            raise ValueError("summary cannot be empty")
        return value

    @field_validator("content", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and chain-of-thought-like keys."""
        _reject_secret_like_keys(value)
        _reject_chain_of_thought_keys(value)
        return value


class WorkingMemoryWriteRequest(BaseModel):
    """Request to write a short-lived working memory slot."""

    model_config = ConfigDict(extra="forbid")

    slot_id: str | None = None
    focus_session_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    slot_type: WorkingMemorySlotType
    source_type: WorkingMemorySourceType
    source_id: str | None = None
    content: dict[str, Any]
    summary: str = Field(min_length=1)
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    ttl_seconds: int | None = Field(default=None, gt=0)
    pinned: bool = False
    owner_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("summary")
    @classmethod
    def summary_cannot_be_blank(cls, value: str) -> str:
        """Reject blank slot summaries."""
        if not value.strip():
            raise ValueError("summary cannot be empty")
        return value

    @field_validator("content", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and chain-of-thought-like keys."""
        _reject_secret_like_keys(value)
        _reject_chain_of_thought_keys(value)
        return value


class WorkingMemoryQuery(BaseModel):
    """Query for short-lived working memory slots."""

    model_config = ConfigDict(extra="forbid")

    focus_session_id: str | None = None
    scope: list[str] = Field(min_length=1)
    slot_types: list[WorkingMemorySlotType] = Field(default_factory=list)
    source_types: list[WorkingMemorySourceType] = Field(default_factory=list)
    include_expired: bool = False
    pinned_only: bool = False
    limit: int = Field(default=25, ge=1, le=100)


def _reject_secret_like_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError("payload must not contain secret-like keys")
            _reject_secret_like_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_secret_like_keys(nested)


def _reject_chain_of_thought_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _CHAIN_OF_THOUGHT_KEY_PARTS):
                raise ValueError("working memory must not store chain-of-thought")
            _reject_chain_of_thought_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_chain_of_thought_keys(nested)
