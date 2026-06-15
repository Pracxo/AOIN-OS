"""Risk assessment contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RiskLevel = Literal["low", "medium", "high", "critical"]
RiskDecision = Literal["allow", "require_approval", "block"]

_SECRET_KEYS = {"api_key", "apikey", "secret", "token", "password", "private_key"}


class RiskAssessmentRequest(BaseModel):
    """Request to score one generic Brain action."""

    model_config = ConfigDict(extra="forbid")

    risk_assessment_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    requested_risk_level: RiskLevel
    payload: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("action_type", "resource_type")
    @classmethod
    def value_cannot_be_blank(cls, value: str) -> str:
        """Reject blank action or resource types."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("payload", "metadata")
    @classmethod
    def no_secret_like_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys recursively."""
        _reject_secret_like_keys(value)
        return value


class RiskAssessment(BaseModel):
    """Persisted deterministic risk assessment."""

    model_config = ConfigDict(extra="forbid")

    risk_assessment_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    action_type: str
    resource_type: str
    resource_id: str | None = None
    requested_risk_level: RiskLevel
    computed_risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    factors: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    decision: RiskDecision
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


def has_secret_like_key(value: object) -> bool:
    """Return whether a payload contains secret-like keys."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower().replace("-", "_") in _SECRET_KEYS:
                return True
            if has_secret_like_key(nested):
                return True
    if isinstance(value, list):
        return any(has_secret_like_key(item) for item in value)
    return False


def _reject_secret_like_keys(value: object) -> None:
    if has_secret_like_key(value):
        raise ValueError("payload must not contain secret-like keys")
