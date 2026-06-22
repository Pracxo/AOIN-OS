"""Attention, focus, interrupt, and context budget contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

FocusStatus = Literal["active", "paused", "ended"]
FocusType = Literal["general", "goal", "task", "workflow", "trace", "replay", "review"]
AttentionRiskLevel = Literal["low", "medium", "high", "critical"]
AttentionSignalType = Literal[
    "user_goal",
    "event_received",
    "task_due",
    "workflow_due",
    "approval_pending",
    "policy_block",
    "risk_alert",
    "memory_conflict",
    "evidence_update",
    "execution_failed",
    "regression_drift",
    "replay_drift",
    "skill_candidate",
    "system_diagnostic",
    "generic",
]
AttentionDecisionType = Literal["focus", "defer", "interrupt", "continue", "clarify", "block"]
InterruptType = Literal[
    "urgent_user_input",
    "approval_required",
    "policy_block",
    "execution_failed",
    "workflow_failed",
    "memory_conflict",
    "regression_drift",
    "system_degraded",
    "generic",
]
InterruptStatus = Literal["pending", "accepted", "deferred", "dismissed", "resolved"]
InterruptDecisionValue = Literal["accept", "defer", "dismiss", "resolve"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
    "authorization",
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


class FocusSession(BaseModel):
    """A persisted cognitive focus session."""

    model_config = ConfigDict(extra="forbid")

    focus_session_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: FocusStatus
    focus_type: FocusType
    active_goal_id: str | None = None
    active_task_id: str | None = None
    active_workflow_run_id: str | None = None
    active_trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    paused_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("title", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank focus text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class FocusSessionCreateRequest(BaseModel):
    """Request to create a cognitive focus session."""

    model_config = ConfigDict(extra="forbid")

    focus_session_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    focus_type: FocusType = "general"
    active_goal_id: str | None = None
    active_task_id: str | None = None
    active_workflow_run_id: str | None = None
    active_trace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=list)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank focus text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class FocusTransitionRequest(BaseModel):
    """Request to transition focus status."""

    model_config = ConfigDict(extra="forbid")

    focus_session_id: str = Field(min_length=1)
    to_status: FocusStatus
    actor_id: str | None = None
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Reject blank transition reasons."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class AttentionSignal(BaseModel):
    """A normalized signal competing for AION focus."""

    model_config = ConfigDict(extra="forbid")

    attention_signal_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    signal_type: AttentionSignalType
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    title: str = Field(min_length=1)
    payload: dict[str, Any]
    urgency: float = Field(ge=0.0, le=1.0)
    importance: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: AttentionRiskLevel
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    handled_at: datetime | None = None

    @field_validator("title", "source_type")
    @classmethod
    def text_cannot_be_blank_or_domain_specific(cls, value: str) -> str:
        """Reject blank or domain-specific signal text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms(value)
        return value

    @field_validator("payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and domain-specific payloads."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class AttentionSignalCreateRequest(BaseModel):
    """Request to create an attention signal."""

    model_config = ConfigDict(extra="forbid")

    attention_signal_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    signal_type: AttentionSignalType
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    title: str = Field(min_length=1)
    payload: dict[str, Any]
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    risk_level: AttentionRiskLevel = "medium"
    owner_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "source_type")
    @classmethod
    def text_cannot_be_blank_or_domain_specific(cls, value: str) -> str:
        """Reject blank or domain-specific signal text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms(value)
        return value

    @field_validator("payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and domain-specific payloads."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class AttentionDecisionRequest(BaseModel):
    """Request to decide current cognitive focus."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    focus_session_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    goal: str | None = None
    intent_type: str | None = None
    scope: list[str] = Field(min_length=1)
    max_signals: int = Field(default=10, ge=0, le=50)
    max_slots: int = Field(default=20, ge=0, le=100)
    include_memory: bool = True
    include_evidence: bool = True
    include_skills: bool = True
    include_capabilities: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class AttentionDecision(BaseModel):
    """Persisted result of deterministic attention selection."""

    model_config = ConfigDict(extra="forbid")

    attention_decision_id: str = Field(min_length=1)
    trace_id: str | None = None
    focus_session_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    decision_type: AttentionDecisionType
    selected_signal_ids: list[str] = Field(default_factory=list)
    selected_slot_ids: list[str] = Field(default_factory=list)
    selected_memory_ids: list[str] = Field(default_factory=list)
    selected_evidence_ids: list[str] = Field(default_factory=list)
    selected_skill_ids: list[str] = Field(default_factory=list)
    selected_capability_ids: list[str] = Field(default_factory=list)
    priority_score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Reject blank decision reasons."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class ContextBudget(BaseModel):
    """Deterministic context allocation for one reasoning packet."""

    model_config = ConfigDict(extra="forbid")

    context_budget_id: str = Field(min_length=1)
    trace_id: str | None = None
    focus_session_id: str | None = None
    intent_id: str | None = None
    context_id: str | None = None
    max_items: int = Field(gt=0)
    max_chars: int = Field(gt=0)
    allocation: dict[str, int]
    used_items: int = Field(ge=0)
    used_chars: int = Field(ge=0)
    overflow_items: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    created_at: datetime | None = None

    @field_validator("allocation")
    @classmethod
    def allocation_values_must_be_non_negative(cls, value: dict[str, int]) -> dict[str, int]:
        """Reject negative source allocations."""
        if any(amount < 0 for amount in value.values()):
            raise ValueError("allocation values must be >= 0")
        return value


class ContextBudgetRequest(BaseModel):
    """Request to allocate a deterministic context budget."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    focus_session_id: str | None = None
    intent_id: str | None = None
    context_id: str | None = None
    scope: list[str] = Field(min_length=1)
    max_items: int = Field(default=20, gt=0)
    max_chars: int = Field(default=12000, gt=0)
    requested_sources: list[str] = Field(default_factory=list)
    priority_weights: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("priority_weights")
    @classmethod
    def weights_must_be_non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        """Reject negative priority weights."""
        if any(weight < 0 for weight in value.values()):
            raise ValueError("priority weights must be >= 0")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class InterruptRecord(BaseModel):
    """Persisted interrupt routed by AION attention control."""

    model_config = ConfigDict(extra="forbid")

    interrupt_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    focus_session_id: str | None = None
    interrupt_type: InterruptType
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    status: InterruptStatus
    priority_score: float = Field(ge=0.0, le=1.0)
    payload: dict[str, Any]
    decision: dict[str, Any]
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("source_type")
    @classmethod
    def source_type_cannot_be_blank_or_domain_specific(cls, value: str) -> str:
        """Reject blank or domain-specific source types."""
        if not value.strip():
            raise ValueError("source_type cannot be empty")
        _reject_domain_terms(value)
        return value

    @field_validator("payload", "decision")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and domain-specific payloads."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class InterruptCreateRequest(BaseModel):
    """Request to create an interrupt record."""

    model_config = ConfigDict(extra="forbid")

    interrupt_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    focus_session_id: str | None = None
    interrupt_type: InterruptType
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    payload: dict[str, Any]
    owner_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_type")
    @classmethod
    def source_type_cannot_be_blank_or_domain_specific(cls, value: str) -> str:
        """Reject blank or domain-specific source types."""
        if not value.strip():
            raise ValueError("source_type cannot be empty")
        _reject_domain_terms(value)
        return value

    @field_validator("payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and domain-specific payloads."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class InterruptDecisionRequest(BaseModel):
    """Request to decide a pending interrupt."""

    model_config = ConfigDict(extra="forbid")

    interrupt_id: str = Field(min_length=1)
    decision: InterruptDecisionValue
    actor_id: str | None = None
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Reject blank interrupt decision reasons."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


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


def _reject_domain_terms(value: Any) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in _BANNED_DOMAIN_TERMS):
            raise ValueError("domain-specific attention logic is not allowed")
    elif isinstance(value, dict):
        for key, nested in value.items():
            _reject_domain_terms(str(key))
            _reject_domain_terms(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_domain_terms(nested)
