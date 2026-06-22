"""Guardrail contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.approvals import ApprovalRequest
from aion_brain.contracts.risk import RiskAssessment, RiskAssessmentRequest, RiskLevel

GuardrailStatus = Literal["active", "disabled"]
GuardrailEffect = Literal["allow", "require_approval", "block"]
GuardrailSeverity = Literal["low", "medium", "high", "critical"]
RiskGuardrailFinalDecision = Literal["allow", "require_approval", "block"]

_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "hr",
    "procurement",
}
_SECRET_KEYS = {"api_key", "apikey", "secret", "token", "password", "private_key"}


class GuardrailRule(BaseModel):
    """A deterministic generic guardrail rule."""

    model_config = ConfigDict(extra="forbid")

    guardrail_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: GuardrailStatus
    scope: list[str] = Field(min_length=1)
    action_types: list[str] = Field(min_length=1)
    resource_types: list[str] = Field(min_length=1)
    risk_levels: list[RiskLevel] = Field(min_length=1)
    conditions: dict[str, Any] = Field(default_factory=dict)
    effect: GuardrailEffect
    severity: GuardrailSeverity
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("action_types", "resource_types")
    @classmethod
    def no_domain_specific_terms(cls, value: list[str]) -> list[str]:
        """Reject domain-specific action or resource terms."""
        for item in value:
            lowered = item.lower()
            if any(term in lowered for term in _BANNED_DOMAIN_TERMS):
                raise ValueError("guardrail rules must remain domain-neutral")
        return value

    @field_validator("metadata")
    @classmethod
    def no_secret_like_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        if _has_secret_like_key(value):
            raise ValueError("metadata must not contain secret-like keys")
        return value


class GuardrailDecision(BaseModel):
    """Result of evaluating generic guardrails."""

    model_config = ConfigDict(extra="forbid")

    guardrail_decision_id: str
    trace_id: str | None = None
    risk_assessment_id: str | None = None
    action_type: str
    resource_type: str
    resource_id: str | None = None
    matched_guardrails: list[str] = Field(default_factory=list)
    allow: bool
    approval_required: bool
    blocked: bool
    severity: GuardrailSeverity
    reason: str
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class RiskGuardrailEvaluationRequest(BaseModel):
    """Request to assess risk, evaluate guardrails, and maybe request approval."""

    model_config = ConfigDict(extra="forbid")

    risk: RiskAssessmentRequest
    approval_hint: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskGuardrailEvaluation(BaseModel):
    """Combined risk, guardrail, and optional approval evaluation."""

    model_config = ConfigDict(extra="forbid")

    risk_assessment: RiskAssessment
    guardrail_decision: GuardrailDecision
    approval_request: ApprovalRequest | None = None
    final_decision: RiskGuardrailFinalDecision
    reason: str
    created_at: datetime


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
