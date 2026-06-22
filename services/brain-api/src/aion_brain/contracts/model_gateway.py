"""Provider-neutral model gateway contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.reasoning import (
    ModelCallRecord,
    ModelRouteDecision,
    PromptPacket,
    ReasoningMode,
    ReasoningRiskLevel,
)

ModelProviderType = Literal[
    "deterministic",
    "litellm_http",
    "openai_compatible_http",
    "local_http",
    "placeholder",
]
ModelProviderStatus = Literal["active", "disabled"]
ModelProviderHealthStatus = Literal["unknown", "healthy", "degraded", "unhealthy"]
ModelPrivacyLevel = Literal["local", "private_gateway", "external"]
ModelLatencyClass = Literal["low", "medium", "high"]
ModelGatewayStatus = Literal[
    "completed",
    "blocked_by_policy",
    "blocked_by_budget",
    "blocked_by_redaction",
    "provider_unavailable",
    "failed",
    "fallback_used",
]
ModelBudgetType = Literal["daily", "weekly", "monthly", "project", "session"]
ModelBudgetStatus = Literal["active", "disabled", "exceeded"]
ModelUsageStatus = Literal["estimated", "recorded", "failed", "blocked"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
    "authorization",
}
_SECRET_VALUE_MARKERS = ("sk-", "bearer ", "authorization=", "api_key=", "token=")


class ModelProvider(BaseModel):
    """Registered provider boundary for model inference."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    provider_type: ModelProviderType
    display_name: str = Field(min_length=1)
    status: ModelProviderStatus
    endpoint_ref: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    health_status: ModelProviderHealthStatus = "unknown"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_health_check_at: datetime | None = None

    @field_validator("endpoint_ref")
    @classmethod
    def endpoint_ref_must_not_contain_secrets(cls, value: str | None) -> str | None:
        """Reject endpoint references that inline credentials."""
        if value is not None and _contains_secret_like_value(value):
            raise ValueError("endpoint_ref must not contain secrets")
        return value

    @field_validator("config")
    @classmethod
    def config_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject provider config that stores credentials directly."""
        _reject_secret_like_keys(value, "config must not contain secret-like keys")
        return value


class ModelProfile(BaseModel):
    """A provider model profile available to the gateway router."""

    model_config = ConfigDict(extra="forbid")

    model_profile_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    mode: ReasoningMode
    status: ModelProviderStatus
    privacy_level: ModelPrivacyLevel
    risk_level: ReasoningRiskLevel
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    cost_per_1k_input_tokens: float | None = Field(default=None, ge=0.0)
    cost_per_1k_output_tokens: float | None = Field(default=None, ge=0.0)
    latency_class: ModelLatencyClass
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject profile metadata that stores credentials directly."""
        _reject_secret_like_keys(value, "metadata must not contain secret-like keys")
        return value


class ModelGatewayRequest(BaseModel):
    """Provider-neutral request to complete a prompt packet."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    trace_id: str | None = None
    reasoning_id: str | None = None
    prompt: PromptPacket
    mode: ReasoningMode
    risk_level: ReasoningRiskLevel
    actor_id: str | None = None
    workspace_id: str | None = None
    scope: list[str] = Field(min_length=1)
    preferred_profile_id: str | None = None
    allow_external: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptRedactionRecord(BaseModel):
    """Prompt inspection and redaction ledger record."""

    model_config = ConfigDict(extra="forbid")

    redaction_id: str = Field(min_length=1)
    trace_id: str | None = None
    reasoning_id: str | None = None
    prompt_id: str | None = None
    redaction_count: int = Field(ge=0)
    redaction_types: list[str]
    blocked: bool
    reason: str | None = None
    created_at: datetime | None = None


class ModelBudgetRecord(BaseModel):
    """Local model budget record used by the gateway guard."""

    model_config = ConfigDict(extra="forbid")

    budget_id: str = Field(min_length=1)
    workspace_id: str | None = None
    actor_id: str | None = None
    scope: list[str] = Field(min_length=1)
    budget_type: ModelBudgetType
    limit_amount: float = Field(ge=0.0)
    used_amount: float = Field(ge=0.0)
    currency: str = Field(min_length=1)
    status: ModelBudgetStatus
    resets_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject budget metadata that stores credentials directly."""
        _reject_secret_like_keys(value, "metadata must not contain secret-like keys")
        return value


class ModelUsageRecord(BaseModel):
    """Model usage and cost estimate ledger record."""

    model_config = ConfigDict(extra="forbid")

    usage_id: str = Field(min_length=1)
    trace_id: str | None = None
    reasoning_id: str | None = None
    model_call_id: str | None = None
    provider_id: str = Field(min_length=1)
    model_profile_id: str | None = None
    model_name: str = Field(min_length=1)
    mode: ReasoningMode
    input_token_estimate: int = Field(ge=0)
    output_token_estimate: int = Field(ge=0)
    cost_estimate: float = Field(ge=0.0)
    latency_ms: int | None = Field(default=None, ge=0)
    status: ModelUsageStatus
    actor_id: str | None = None
    workspace_id: str | None = None
    created_at: datetime | None = None


class ModelProviderHealth(BaseModel):
    """Provider health check result."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    status: ModelProviderHealthStatus
    latency_ms: int | None = Field(default=None, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime


class ModelGatewayResponse(BaseModel):
    """Provider-neutral model gateway completion response."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    model_call: ModelCallRecord
    usage: ModelUsageRecord
    redaction: PromptRedactionRecord | None = None
    route_decision: ModelRouteDecision
    output: dict[str, Any]
    status: ModelGatewayStatus
    reason: str | None = None
    created_at: datetime


def _reject_secret_like_keys(value: object, message: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(secret in normalized for secret in _SECRET_KEY_PARTS):
                raise ValueError(message)
            _reject_secret_like_keys(nested, message)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_like_keys(item, message)


def _contains_secret_like_value(value: str) -> bool:
    normalized = value.lower()
    return any(marker in normalized for marker in _SECRET_VALUE_MARKERS)
