"""Model provider hardening contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text

ProviderProfileStatus = Literal["proposed", "ready_for_review", "blocked", "disabled", "archived"]
ProviderType = Literal[
    "metadata_only",
    "dry_run_simulator",
    "local_stub",
    "external_provider_preview",
    "generic",
]
ProviderRiskLevel = Literal["low", "medium", "high", "critical"]
PreviewStatus = Literal["passed", "warning", "blocked", "failed"]
SimulationStatus = Literal["passed", "warning", "blocked", "failed", "dry_run"]
ReadinessStatus = Literal["ready_for_review", "warning", "blocked", "failed"]
ReadinessLevel = Literal["metadata_only", "dry_run_ready", "blocked", "not_ready"]
ProviderBlockerType = Literal[
    "external_calls_disabled",
    "credentials_missing",
    "credential_storage_forbidden",
    "raw_prompt_detected",
    "hidden_reasoning_detected",
    "output_governance_missing",
    "tool_intent_guard_missing",
    "grounding_required",
    "policy_action_missing",
    "audit_required",
    "provider_activation_disabled",
    "unsafe_metadata",
    "generic",
]
ProviderBlockerSeverity = Literal["low", "medium", "high", "critical"]
ProviderBlockerStatus = Literal["open", "resolved", "dismissed", "archived"]

_DOTTED_LOWER_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")


class ModelProviderProfile(BaseModel):
    """Metadata-only provider profile. This is never provider activation."""

    model_config = ConfigDict(extra="forbid")

    provider_profile_id: str = Field(min_length=1)
    provider_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ProviderProfileStatus
    provider_type: ProviderType
    owner_scope: list[str] = Field(min_length=1)
    supported_model_families: list[str] = Field(default_factory=list)
    supported_modes: list[str] = Field(default_factory=list)
    declared_capabilities: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    egress_requirements: list[str] = Field(default_factory=list)
    output_governance_requirements: list[str] = Field(default_factory=list)
    grounding_requirements: list[str] = Field(default_factory=list)
    tool_use_policy: dict[str, Any] = Field(default_factory=dict)
    risk_level: ProviderRiskLevel
    external_calls_allowed: bool
    credentials_required: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("provider_key")
    @classmethod
    def provider_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("provider_key must be dotted lowercase text")
        return value

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        reject_hidden_or_secret_text(cleaned, "model provider profile text")
        return cleaned

    @field_validator(
        "supported_model_families",
        "supported_modes",
        "declared_capabilities",
        "required_settings",
        "required_policy_actions",
        "egress_requirements",
        "output_governance_requirements",
        "grounding_requirements",
    )
    @classmethod
    def list_items_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "model provider list item")
        return value

    @field_validator("tool_use_policy", "metadata")
    @classmethod
    def dicts_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value

    @model_validator(mode="after")
    def profile_must_remain_inactive(self) -> ModelProviderProfile:
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false in AION-086")
        if self.credentials_required:
            raise ValueError("credentials_required must be false in AION-086")
        _reject_activation_markers(self.metadata)
        _reject_activation_markers(self.tool_use_policy)
        return self


class ModelProviderProfileCreateRequest(BaseModel):
    """Create provider readiness metadata without enabling a provider."""

    model_config = ConfigDict(extra="forbid")

    provider_profile_id: str | None = None
    provider_key: str
    name: str
    description: str
    provider_type: ProviderType = "metadata_only"
    owner_scope: list[str] = Field(min_length=1)
    supported_model_families: list[str] = Field(default_factory=list)
    supported_modes: list[str] = Field(default_factory=lambda: ["dry_run"])
    declared_capabilities: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    egress_requirements: list[str] = Field(default_factory=list)
    output_governance_requirements: list[str] = Field(default_factory=list)
    grounding_requirements: list[str] = Field(default_factory=list)
    tool_use_policy: dict[str, Any] = Field(default_factory=dict)
    risk_level: ProviderRiskLevel = "medium"
    external_calls_allowed: bool = False
    credentials_required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("provider_key")
    @classmethod
    def provider_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("provider_key must be dotted lowercase text")
        return value

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        reject_hidden_or_secret_text(cleaned, "model provider profile text")
        return cleaned

    @field_validator("tool_use_policy", "metadata")
    @classmethod
    def dicts_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value

    @model_validator(mode="after")
    def create_request_must_remain_inactive(self) -> ModelProviderProfileCreateRequest:
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false in AION-086")
        if self.credentials_required:
            raise ValueError("credentials_required must be false in AION-086")
        _reject_activation_markers(self.metadata)
        return self


class ModelProviderProfileSeedRequest(BaseModel):
    """Seed or preview default provider-hardening profiles."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    dry_run: bool = True
    created_by: str | None = None


class PromptEgressPreviewRequest(BaseModel):
    """Request a local-only prompt egress preview."""

    model_config = ConfigDict(extra="forbid")

    prompt_egress_preview_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    provider_profile_id: str | None = None
    provider_key: str
    preview_type: str = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    prompt_packet_ref: str | None = None
    input_manifest_ref: str | None = None
    prompt_summary: dict[str, Any] = Field(default_factory=dict)
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("provider_key")
    @classmethod
    def provider_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("provider_key must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value


class PromptEgressPreview(BaseModel):
    """Persisted prompt egress preview with redacted summary only."""

    model_config = ConfigDict(extra="forbid")

    prompt_egress_preview_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    provider_profile_id: str | None = None
    provider_key: str
    status: PreviewStatus
    preview_type: str
    owner_scope: list[str] = Field(min_length=1)
    prompt_packet_ref: str | None = None
    input_manifest_ref: str | None = None
    redacted_prompt_summary: dict[str, Any]
    blocked_fields: list[str] = Field(default_factory=list)
    egress_allowed: bool
    external_call_allowed: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("redacted_prompt_summary", "metadata")
    @classmethod
    def stored_payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value

    @model_validator(mode="after")
    def preview_cannot_allow_external_call(self) -> PromptEgressPreview:
        if self.external_call_allowed:
            raise ValueError("external_call_allowed must be false in AION-086")
        return self


class ModelProviderSimulationRequest(BaseModel):
    """Request a deterministic dry-run provider simulation."""

    model_config = ConfigDict(extra="forbid")

    provider_simulation_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    provider_profile_id: str | None = None
    provider_key: str
    simulation_type: str = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    input_manifest_ref: str | None = None
    egress_preview_id: str | None = None
    simulated_request: dict[str, Any] = Field(default_factory=dict)
    expected_response_shape: dict[str, Any] = Field(default_factory=dict)
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("provider_key")
    @classmethod
    def provider_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("provider_key must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value


class ModelProviderSimulation(BaseModel):
    """Persisted local-only provider simulation."""

    model_config = ConfigDict(extra="forbid")

    provider_simulation_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    provider_profile_id: str | None = None
    provider_key: str
    status: SimulationStatus
    simulation_type: str
    owner_scope: list[str] = Field(min_length=1)
    input_manifest_ref: str | None = None
    egress_preview_id: str | None = None
    simulated_request_hash: str
    simulated_response_hash: str
    redacted_simulated_request: dict[str, Any]
    redacted_simulated_response: dict[str, Any]
    output_governance_status: str
    tool_intent_status: str
    grounding_status: str
    external_calls_made: bool
    credentials_used: bool
    model_invoked: bool
    score: float = Field(ge=0.0, le=1.0)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("redacted_simulated_request", "redacted_simulated_response", "metadata")
    @classmethod
    def stored_payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value

    @model_validator(mode="after")
    def simulation_must_not_call_provider(self) -> ModelProviderSimulation:
        if self.external_calls_made:
            raise ValueError("external_calls_made must be false")
        if self.credentials_used:
            raise ValueError("credentials_used must be false")
        if self.model_invoked:
            raise ValueError("model_invoked must be false")
        return self


class ModelProviderReadinessRequest(BaseModel):
    """Assess readiness without enabling provider calls."""

    model_config = ConfigDict(extra="forbid")

    provider_readiness_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    provider_profile_id: str | None = None
    provider_key: str
    owner_scope: list[str] = Field(min_length=1)
    simulation_refs: list[str] = Field(default_factory=list)
    require_egress_guard: bool = True
    require_output_governance: bool = True
    require_tool_intent_guard: bool = True
    require_grounding: bool = True
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("provider_key")
    @classmethod
    def provider_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("provider_key must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value


class ModelProviderReadiness(BaseModel):
    """Provider-readiness assessment. This never enables a provider."""

    model_config = ConfigDict(extra="forbid")

    provider_readiness_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    provider_profile_id: str | None = None
    provider_key: str
    status: ReadinessStatus
    readiness_level: ReadinessLevel
    owner_scope: list[str] = Field(min_length=1)
    external_call_ready: bool
    credentials_ready: bool
    egress_guard_ready: bool
    output_governance_ready: bool
    tool_intent_guard_ready: bool
    grounding_ready: bool
    policy_ready: bool
    audit_ready: bool
    blocker_refs: list[str] = Field(default_factory=list)
    warning_refs: list[str] = Field(default_factory=list)
    simulation_refs: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value

    @model_validator(mode="after")
    def readiness_must_not_enable_external_calls(self) -> ModelProviderReadiness:
        if self.external_call_ready:
            raise ValueError("external_call_ready must be false in AION-086")
        if self.credentials_ready:
            raise ValueError("credentials_ready must be false in AION-086")
        return self


class ModelProviderBlocker(BaseModel):
    """Local blocker record for provider hardening."""

    model_config = ConfigDict(extra="forbid")

    provider_blocker_id: str
    trace_id: str | None = None
    provider_profile_id: str | None = None
    provider_key: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    blocker_type: ProviderBlockerType
    severity: ProviderBlockerSeverity
    status: ProviderBlockerStatus
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("reason", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "model provider blocker text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_provider_payload_secrets(value)
        return value


class ModelProviderBlockerDismissRequest(BaseModel):
    """Dismiss a blocker without enabling provider behavior."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderHardeningQuery(BaseModel):
    """Aggregate provider hardening metadata."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    provider_key: str | None = None
    status: str | None = None
    risk_level: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class ProviderHardeningQueryResult(BaseModel):
    """Query result for provider hardening metadata."""

    model_config = ConfigDict(extra="forbid")

    profiles: list[ModelProviderProfile]
    egress_previews: list[PromptEgressPreview]
    simulations: list[ModelProviderSimulation]
    readiness_assessments: list[ModelProviderReadiness]
    blockers: list[ModelProviderBlocker]
    total_count: int
    constraints: list[str]
    metadata: dict[str, Any]


_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "password",
    "private_key",
    "secret",
    "token",
}
_FALSE_SAFETY_FLAG_KEYS = {
    "credentials_required",
    "credentials_used",
    "credentials_ready",
    "model_provider_credentials_enabled",
    "raw_prompt_included",
    "raw_prompt_stored",
}
_FALSE_FLAG_KEY_PARTS = {
    "credential",
    "raw_prompt",
}


def reject_provider_payload_secrets(value: object) -> None:
    """Reject secrets while allowing explicit false safety flags."""

    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _FALSE_SAFETY_FLAG_KEYS and nested is False:
                continue
            if any(part in lowered for part in _FALSE_FLAG_KEY_PARTS):
                raise ValueError("provider payload safety flags must be false")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError("provider payload must not contain secret-like keys")
            reject_provider_payload_secrets(nested)
    elif isinstance(value, list):
        for item in value:
            reject_provider_payload_secrets(item)
    elif isinstance(value, str):
        reject_hidden_or_secret_text(value, "provider payload")


def _reject_activation_markers(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in {
                "activated",
                "activation_enabled",
                "provider_enabled",
                "external_calls_allowed",
                "execute",
            } and bool(value):
                raise ValueError("provider metadata must not imply activation")
            _reject_activation_markers(value)
    elif isinstance(payload, list):
        for item in payload:
            _reject_activation_markers(item)


__all__ = [
    "ModelProviderBlocker",
    "ModelProviderBlockerDismissRequest",
    "ModelProviderProfile",
    "ModelProviderProfileCreateRequest",
    "ModelProviderProfileSeedRequest",
    "ModelProviderReadiness",
    "ModelProviderReadinessRequest",
    "ModelProviderSimulation",
    "ModelProviderSimulationRequest",
    "PromptEgressPreview",
    "PromptEgressPreviewRequest",
    "ProviderHardeningQuery",
    "ProviderHardeningQueryResult",
]
