"""Autonomy Governor contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AutonomyMode = Literal[
    "disabled",
    "observe",
    "assist",
    "plan_only",
    "dry_run",
    "supervised_controlled",
    "delegated_controlled",
]
AutonomyRiskLevel = Literal["low", "medium", "high", "critical"]
AutonomyProfileStatus = Literal["active", "disabled"]
RunLevelStatus = Literal["active", "expired", "ended"]
DelegationStatus = Literal["active", "revoked", "expired"]
AutonomyLifecycleEventType = Literal[
    "autonomy_profile_created",
    "autonomy_profile_disabled",
    "run_level_set",
    "run_level_ended",
    "delegation_created",
    "delegation_revoked",
    "autonomy_decision_recorded",
    "autonomy_blocked",
    "autonomy_escalation_required",
]
DEFAULT_APPROVAL_REQUIRED_MODES: list[AutonomyMode] = [
    "supervised_controlled",
    "delegated_controlled",
]

ALLOWED_MODES: set[str] = {
    "disabled",
    "observe",
    "assist",
    "plan_only",
    "dry_run",
    "supervised_controlled",
    "delegated_controlled",
}
ALLOWED_RISK_LEVELS: set[str] = {"low", "medium", "high", "critical"}
_CONTROLLED_MODES = {"supervised_controlled", "delegated_controlled"}
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


class AutonomyProfile(BaseModel):
    """A reusable autonomy envelope for an actor or workspace."""

    model_config = ConfigDict(extra="forbid")

    autonomy_profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: AutonomyProfileStatus
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    default_mode: AutonomyMode
    max_mode: AutonomyMode
    max_risk_level: AutonomyRiskLevel
    allowed_action_types: list[str] = Field(default_factory=list)
    denied_action_types: list[str] = Field(default_factory=list)
    external_models_allowed: bool = False
    external_tools_allowed: bool = False
    background_workflows_allowed: bool = False
    scheduler_allowed: bool = False
    skill_promotion_allowed: bool = False
    memory_forgetting_allowed: bool = False
    approval_required_modes: list[AutonomyMode] = Field(default_factory=list)
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

    @field_validator("allowed_action_types", "denied_action_types")
    @classmethod
    def action_types_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject vertical action names."""
        _reject_domain_terms(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class AutonomyProfileCreateRequest(BaseModel):
    """Request to create an autonomy profile."""

    model_config = ConfigDict(extra="forbid")

    autonomy_profile_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=list)
    default_mode: AutonomyMode = "assist"
    max_mode: AutonomyMode = "dry_run"
    max_risk_level: AutonomyRiskLevel = "medium"
    allowed_action_types: list[str] = Field(default_factory=list)
    denied_action_types: list[str] = Field(default_factory=list)
    external_models_allowed: bool = False
    external_tools_allowed: bool = False
    background_workflows_allowed: bool = False
    scheduler_allowed: bool = False
    skill_promotion_allowed: bool = False
    memory_forgetting_allowed: bool = False
    approval_required_modes: list[AutonomyMode] = Field(
        default_factory=lambda: list(DEFAULT_APPROVAL_REQUIRED_MODES)
    )
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    activate: bool = True

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank fields."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("allowed_action_types", "denied_action_types")
    @classmethod
    def action_types_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject vertical action names."""
        _reject_domain_terms(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class RunLevelRecord(BaseModel):
    """A time-bounded operating mode override."""

    model_config = ConfigDict(extra="forbid")

    run_level_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    active_profile_id: str | None = None
    run_level: AutonomyMode
    status: RunLevelStatus
    reason: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    set_by: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    ended_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Require a reason."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class SetRunLevelRequest(BaseModel):
    """Request to set an active run level."""

    model_config = ConfigDict(extra="forbid")

    run_level_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    active_profile_id: str | None = None
    run_level: AutonomyMode
    reason: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    set_by: str | None = None
    expires_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_cannot_be_blank(cls, value: str) -> str:
        """Require a reason."""
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class DelegationGrant(BaseModel):
    """A bounded delegation for controlled autonomy."""

    model_config = ConfigDict(extra="forbid")

    delegation_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    delegated_by: str | None = None
    delegated_to: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    mode: AutonomyMode
    max_risk_level: AutonomyRiskLevel
    allowed_action_types: list[str] = Field(default_factory=list)
    resource_types: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    status: DelegationStatus
    reason: str = Field(min_length=1)
    created_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_delegation_mode(self) -> "DelegationGrant":
        """Delegations only cover controlled modes."""
        if self.mode not in _CONTROLLED_MODES:
            raise ValueError("delegation mode must be controlled")
        _reject_domain_terms(self.resource_types)
        _reject_domain_terms(self.allowed_action_types)
        return self


class DelegationGrantRequest(BaseModel):
    """Request to create a delegation grant."""

    model_config = ConfigDict(extra="forbid")

    delegation_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    delegated_by: str | None = None
    delegated_to: str | None = None
    owner_scope: list[str] = Field(default_factory=list)
    mode: AutonomyMode = "supervised_controlled"
    max_risk_level: AutonomyRiskLevel = "medium"
    allowed_action_types: list[str] = Field(default_factory=list)
    resource_types: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_request(self) -> "DelegationGrantRequest":
        """Validate controlled mode and generic scope."""
        if self.mode not in _CONTROLLED_MODES:
            raise ValueError("delegation mode must be controlled")
        if not self.reason.strip():
            raise ValueError("reason cannot be empty")
        _reject_domain_terms(self.resource_types)
        _reject_domain_terms(self.allowed_action_types)
        return self


class AutonomyDecisionRequest(BaseModel):
    """Request to resolve one action against autonomy constraints."""

    model_config = ConfigDict(extra="forbid")

    autonomy_decision_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    requested_mode: AutonomyMode
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    risk_level: AutonomyRiskLevel
    approval_present: bool = False
    delegation_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("action_type", "resource_type")
    @classmethod
    def values_must_be_generic(cls, value: str) -> str:
        """Reject empty or vertical action/resource names."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms([value])
        return value

    @field_validator("context", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like payloads."""
        _reject_secret_like_keys(value)
        return value


class AutonomyDecision(BaseModel):
    """A persisted autonomy decision."""

    model_config = ConfigDict(extra="forbid")

    autonomy_decision_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    requested_mode: AutonomyMode
    resolved_mode: AutonomyMode
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    risk_level: AutonomyRiskLevel
    allow: bool
    approval_required: bool
    delegation_id: str | None = None
    autonomy_profile_id: str | None = None
    run_level_id: str | None = None
    reason: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class AutonomyStatus(BaseModel):
    """Current autonomy state for an actor/workspace."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    workspace_id: str | None = None
    active_profile: AutonomyProfile | None = None
    active_run_level: RunLevelRecord | None = None
    active_delegations: list[DelegationGrant] = Field(default_factory=list)
    effective_mode: AutonomyMode
    max_risk_level: AutonomyRiskLevel
    constraints: list[str] = Field(default_factory=list)
    generated_at: datetime


class AutonomyLifecycleEvent(BaseModel):
    """Autonomy lifecycle telemetry and audit event."""

    model_config = ConfigDict(extra="forbid")

    autonomy_event_id: str = Field(min_length=1)
    autonomy_profile_id: str | None = None
    run_level_id: str | None = None
    delegation_id: str | None = None
    autonomy_decision_id: str | None = None
    trace_id: str | None = None
    event_type: AutonomyLifecycleEventType
    actor_id: str | None = None
    workspace_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("payload")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like payloads."""
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


def _reject_domain_terms(values: list[str]) -> None:
    for value in values:
        lowered = value.lower()
        if any(term in lowered for term in _BANNED_DOMAIN_TERMS):
            raise ValueError("autonomy contracts must stay domain-neutral")
