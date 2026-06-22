"""Event reaction router contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.events import AIONEvent

EventTriggerRuleType = Literal[
    "event_type",
    "source",
    "actor",
    "workspace",
    "payload_key_exists",
    "payload_value_equals",
    "payload_value_in",
    "security_scope_contains",
    "correlation_present",
    "trace_present",
    "risk_level_hint",
    "generic",
]
EventTriggerOperator = Literal[
    "equals",
    "not_equals",
    "in",
    "not_in",
    "exists",
    "contains",
    "starts_with",
    "ends_with",
]
EventSubscriptionStatus = Literal["active", "disabled"]
EventReactionTargetType = Literal[
    "attention_signal",
    "interrupt",
    "task",
    "workflow",
    "cognitive_cycle",
    "memory_governance",
    "capability",
    "trace",
    "noop",
]
EventReactionMode = Literal["dry_run", "controlled"]
EventReactionRiskLevel = Literal["low", "medium", "high", "critical"]
EventReactionActionStatus = Literal[
    "pending",
    "running",
    "completed",
    "dry_run",
    "skipped",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "waiting_for_approval",
    "failed",
]
EventDispatchStatus = Literal[
    "pending",
    "running",
    "completed",
    "partially_completed",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "failed",
    "dry_run",
]
EventDeadLetterStatus = Literal["open", "replayed", "resolved", "dismissed"]

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
_FIELD_PATH_FORBIDDEN = {"[", "]", "(", ")", "{", "}", ";", ":", "`", "$", "|", "&"}


class EventTriggerRule(BaseModel):
    """A deterministic predicate against a normalized AION event."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1)
    rule_type: EventTriggerRuleType
    field_path: str | None = None
    operator: EventTriggerOperator
    value: Any | None = None
    values: list[Any] = Field(default_factory=list)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("rule_id")
    @classmethod
    def rule_id_cannot_be_blank(cls, value: str) -> str:
        """Reject blank identifiers."""
        if not value.strip():
            raise ValueError("rule_id cannot be empty")
        return value

    @field_validator("field_path")
    @classmethod
    def field_path_must_be_static(cls, value: str | None) -> str | None:
        """Reject code-like path syntax."""
        if value is None:
            return value
        if not value.strip():
            raise ValueError("field_path cannot be empty")
        if any(part in value for part in _FIELD_PATH_FORBIDDEN):
            raise ValueError("field_path must be a safe dotted path")
        if ".." in value or value.startswith(".") or value.endswith("."):
            raise ValueError("field_path must be a safe dotted path")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class EventSubscription(BaseModel):
    """A policy-gated event reaction subscription."""

    model_config = ConfigDict(extra="forbid")

    subscription_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: EventSubscriptionStatus = "active"
    owner_scope: list[str] = Field(min_length=1)
    source_filters: list[str] = Field(default_factory=list)
    event_type_patterns: list[str] = Field(min_length=1)
    trigger_rules: list[EventTriggerRule] = Field(default_factory=list)
    target_type: EventReactionTargetType
    target_id: str | None = None
    reaction_mode: EventReactionMode = "dry_run"
    risk_level: EventReactionRiskLevel = "low"
    max_actions: int = Field(default=1, ge=1, le=100)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject empty display text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("target_id")
    @classmethod
    def target_must_be_generic(cls, value: str | None) -> str | None:
        """Reject vertical target identifiers."""
        if value is not None:
            _reject_domain_terms(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and vertical metadata."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class EventSubscriptionCreateRequest(BaseModel):
    """Request to register a subscription."""

    model_config = ConfigDict(extra="forbid")

    subscription_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(default_factory=list)
    source_filters: list[str] = Field(default_factory=list)
    event_type_patterns: list[str] = Field(min_length=1)
    trigger_rules: list[EventTriggerRule] = Field(default_factory=list)
    target_type: EventReactionTargetType = "noop"
    target_id: str | None = None
    reaction_mode: EventReactionMode = "dry_run"
    risk_level: EventReactionRiskLevel = "low"
    max_actions: int = Field(default=1, ge=1, le=100)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    activate: bool = True

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject empty display text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("target_id")
    @classmethod
    def target_must_be_generic(cls, value: str | None) -> str | None:
        """Reject vertical target identifiers."""
        if value is not None:
            _reject_domain_terms(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like and vertical metadata."""
        _reject_secret_like_keys(value)
        _reject_domain_terms(value)
        return value


class EventDispatchRequest(BaseModel):
    """Request to manually dispatch one event through the reaction router."""

    model_config = ConfigDict(extra="forbid")

    dispatch_id: str | None = None
    event: AIONEvent | None = None
    event_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: EventReactionMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    subscription_ids: list[str] = Field(default_factory=list)
    max_actions: int = Field(default=25, ge=1, le=100)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_event_or_event_id(self) -> "EventDispatchRequest":
        """Require either an inline event or a ledger event reference."""
        if self.event is None and self.event_id is None:
            raise ValueError("event or event_id is required")
        return self

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class EventReactionAction(BaseModel):
    """One attempted reaction action for a dispatch."""

    model_config = ConfigDict(extra="forbid")

    reaction_action_id: str = Field(min_length=1)
    dispatch_id: str = Field(min_length=1)
    subscription_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    trace_id: str | None = None
    target_type: EventReactionTargetType
    target_id: str | None = None
    action_type: str = Field(min_length=1)
    mode: EventReactionMode
    status: EventReactionActionStatus
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    policy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    autonomy_decision_id: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("input", "output", "error")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like action payloads."""
        _reject_secret_like_keys(value)
        return value


class EventDispatchRecord(BaseModel):
    """Persistent result of a router dispatch."""

    model_config = ConfigDict(extra="forbid")

    dispatch_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: EventDispatchStatus
    mode: EventReactionMode
    matched_subscription_ids: list[str] = Field(default_factory=list)
    actions: list[EventReactionAction] = Field(default_factory=list)
    action_count: int = Field(ge=0)
    completed_action_count: int = Field(ge=0)
    failed_action_count: int = Field(ge=0)
    blocked_action_count: int = Field(ge=0)
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("result")
    @classmethod
    def result_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like result payloads."""
        _reject_secret_like_keys(value)
        return value


class EventDeadLetterRecord(BaseModel):
    """A failed event reaction retained for inspection or replay."""

    model_config = ConfigDict(extra="forbid")

    dead_letter_id: str = Field(min_length=1)
    dispatch_id: str = Field(min_length=1)
    reaction_action_id: str | None = None
    event_id: str = Field(min_length=1)
    subscription_id: str | None = None
    trace_id: str | None = None
    reason: str = Field(min_length=1)
    error: dict[str, Any] = Field(default_factory=dict)
    status: EventDeadLetterStatus = "open"
    replay_count: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Reject blank failure reasons."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("error")
    @classmethod
    def error_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like failure payloads."""
        _reject_secret_like_keys(value)
        return value


class EventRouterStatus(BaseModel):
    """Readiness status for the reaction router control plane."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    auto_dispatch_enabled: bool
    subscription_count: int = Field(ge=0)
    active_subscription_count: int = Field(ge=0)
    pending_dead_letter_count: int = Field(ge=0)
    latest_dispatch_id: str | None = None
    generated_at: datetime


def _reject_secret_like_keys(value: object) -> None:
    secret_key = _find_secret_key(value)
    if secret_key is not None:
        raise ValueError(f"payload must not contain secret-like key: {secret_key}")


def _find_secret_key(value: object) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _SECRET_KEY_PARTS:
                return str(key)
            nested = _find_secret_key(item)
            if nested is not None:
                return nested
    if isinstance(value, list):
        for item in value:
            nested = _find_secret_key(item)
            if nested is not None:
                return nested
    return None


def _reject_domain_terms(value: object) -> None:
    text = _flatten_text(value).lower()
    for term in _BANNED_DOMAIN_TERMS:
        if term in text:
            raise ValueError("event reaction contracts must remain domain-neutral")


def _flatten_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    if value is None:
        return ""
    return str(value)
