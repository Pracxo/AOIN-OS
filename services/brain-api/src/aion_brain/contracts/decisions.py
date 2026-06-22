"""Decision intelligence contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.concepts import reject_secret_like_keys
from aion_brain.contracts.counterfactuals import CounterfactualRun

DecisionFrameStatus = Literal["open", "evaluated", "decided", "closed", "archived"]
DecisionFrameType = Literal[
    "next_action",
    "plan_choice",
    "clarification",
    "risk_response",
    "approval_response",
    "recovery",
    "operator_review",
    "generic",
]
DecisionOptionType = Literal[
    "observe",
    "clarify",
    "retrieve_more_context",
    "create_plan",
    "revise_plan",
    "request_approval",
    "dry_run",
    "controlled_action",
    "defer",
    "no_op",
    "generic",
]
DecisionOptionStatus = Literal["proposed", "evaluated", "recommended", "rejected", "archived"]
DecisionRiskLevel = Literal["low", "medium", "high", "critical"]
DecisionReversibility = Literal[
    "reversible",
    "partially_reversible",
    "irreversible",
    "unknown",
]
UtilityProfileStatus = Literal["active", "disabled"]
OptionEvaluationStatus = Literal["passed", "warning", "blocked", "failed"]
DecisionRecordStatus = Literal["recorded", "superseded", "cancelled"]
DecisionType = Literal[
    "recommendation",
    "human_choice",
    "system_choice",
    "operator_note",
    "deferred",
]

REQUIRED_UTILITY_WEIGHTS = (
    "goal_alignment",
    "evidence_support",
    "belief_confidence",
    "risk_reduction",
    "policy_allowance",
    "autonomy_allowance",
    "reversibility",
    "cost_efficiency",
    "urgency",
    "uncertainty_reduction",
)
DOMAIN_UTILITY_TERMS = {
    "finance",
    "trading",
    "stock",
    "legal",
    "medical",
    "health",
    "healthcare",
    "procurement",
    "payroll",
    "payment",
    "security",
}


class DecisionFrame(BaseModel):
    """A generic frame for choosing among possible next actions."""

    model_config = ConfigDict(extra="forbid")

    decision_frame_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: DecisionFrameStatus = "open"
    frame_type: DecisionFrameType = "generic"
    title: str = Field(min_length=1)
    question: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    situation_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    goal_refs: list[str] = Field(default_factory=list)
    task_refs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class DecisionFrameCreateRequest(BaseModel):
    """Request to create a decision frame."""

    model_config = ConfigDict(extra="forbid")

    decision_frame_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    frame_type: DecisionFrameType = "generic"
    title: str = Field(min_length=1)
    question: str = Field(min_length=1)
    owner_scope: list[str] = Field(default_factory=list)
    situation_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    goal_refs: list[str] = Field(default_factory=list)
    task_refs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class DecisionOption(BaseModel):
    """A generic candidate option within a decision frame."""

    model_config = ConfigDict(extra="forbid")

    decision_option_id: str = Field(min_length=1)
    decision_frame_id: str = Field(min_length=1)
    option_type: DecisionOptionType = "generic"
    status: DecisionOptionStatus = "proposed"
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    action_type: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    expected_effects: list[dict[str, Any]] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    risk_level: DecisionRiskLevel = "medium"
    reversibility: DecisionReversibility = "unknown"
    cost_estimate: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("metadata", "cost_estimate")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @field_validator("expected_effects")
    @classmethod
    def effects_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def controlled_recommendation_requires_gates(self) -> DecisionOption:
        if self.option_type != "controlled_action" or self.status != "recommended":
            return self
        gates = (
            "policy_decision_id",
            "risk_assessment_id",
            "approval_request_id",
            "autonomy_decision_id",
        )
        if not all(self.metadata.get(key) for key in gates):
            raise ValueError("controlled_action cannot be recommended without gates")
        return self


class DecisionOptionCreateRequest(BaseModel):
    """Request to create one decision option."""

    model_config = ConfigDict(extra="forbid")

    decision_option_id: str | None = None
    decision_frame_id: str = Field(min_length=1)
    option_type: DecisionOptionType = "generic"
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    action_type: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    expected_effects: list[dict[str, Any]] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    risk_level: DecisionRiskLevel = "medium"
    reversibility: DecisionReversibility = "unknown"
    cost_estimate: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", "cost_estimate")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @field_validator("expected_effects")
    @classmethod
    def effects_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_keys(value)
        return value


class UtilityProfile(BaseModel):
    """Generic utility weights used for deterministic option scoring."""

    model_config = ConfigDict(extra="forbid")

    utility_profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: UtilityProfileStatus = "active"
    owner_scope: list[str] = Field(min_length=1)
    weights: dict[str, float]
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("weights")
    @classmethod
    def weights_must_be_complete_and_generic(cls, value: dict[str, float]) -> dict[str, float]:
        missing = [key for key in REQUIRED_UTILITY_WEIGHTS if key not in value]
        if missing:
            raise ValueError(f"missing utility weight keys: {missing}")
        unknown = sorted(set(value) - set(REQUIRED_UTILITY_WEIGHTS))
        if unknown:
            if any(_contains_domain_term(key) for key in unknown):
                raise ValueError("utility profile contains domain-specific weight key")
            raise ValueError(f"unknown utility weight keys: {unknown}")
        for key, weight in value.items():
            if weight < 0.0 or weight > 1.0:
                raise ValueError(f"weight out of range: {key}")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class UtilityProfileCreateRequest(BaseModel):
    """Request to create one utility profile."""

    model_config = ConfigDict(extra="forbid")

    utility_profile_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    weights: dict[str, float]
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("weights")
    @classmethod
    def weights_must_be_complete_and_generic(cls, value: dict[str, float]) -> dict[str, float]:
        return UtilityProfile(
            utility_profile_id="validation",
            name="validation",
            description="validation",
            owner_scope=["validation"],
            weights=value,
        ).weights

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class OptionEvaluation(BaseModel):
    """Deterministic evaluation of one option."""

    model_config = ConfigDict(extra="forbid")

    option_evaluation_id: str = Field(min_length=1)
    decision_frame_id: str = Field(min_length=1)
    decision_option_id: str = Field(min_length=1)
    utility_profile_id: str | None = None
    status: OptionEvaluationStatus
    score: float = Field(ge=0.0, le=1.0)
    rank: int | None = None
    factors: dict[str, Any] = Field(default_factory=dict)
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    tradeoffs: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("metadata", "factors", "tradeoffs")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class DecisionEvaluationRequest(BaseModel):
    """Request to evaluate options in one decision frame."""

    model_config = ConfigDict(extra="forbid")

    decision_frame_id: str = Field(min_length=1)
    utility_profile_id: str | None = None
    option_ids: list[str] = Field(default_factory=list)
    include_policy: bool = True
    include_risk: bool = True
    include_autonomy: bool = True
    include_counterfactuals: bool = True
    approval_present: bool = False
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class TradeoffMatrix(BaseModel):
    """Matrix of option scores by generic criteria."""

    model_config = ConfigDict(extra="forbid")

    tradeoff_matrix_id: str = Field(min_length=1)
    decision_frame_id: str = Field(min_length=1)
    utility_profile_id: str | None = None
    option_ids: list[str]
    criteria: list[str]
    scores: dict[str, dict[str, float]]
    recommended_option_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class DecisionRecord(BaseModel):
    """A journal entry recording a recommendation or human/system choice."""

    model_config = ConfigDict(extra="forbid")

    decision_record_id: str = Field(min_length=1)
    decision_frame_id: str = Field(min_length=1)
    selected_option_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: DecisionRecordStatus = "recorded"
    decision_type: DecisionType = "recommendation"
    rationale: str = Field(min_length=1)
    evaluation_refs: list[str] = Field(default_factory=list)
    counterfactual_refs: list[str] = Field(default_factory=list)
    approval_request_id: str | None = None
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    outcome_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    superseded_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class DecisionRecordRequest(BaseModel):
    """Request to record a decision without executing it."""

    model_config = ConfigDict(extra="forbid")

    decision_record_id: str | None = None
    decision_frame_id: str = Field(min_length=1)
    selected_option_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    decision_type: DecisionType = "recommendation"
    rationale: str = Field(min_length=1)
    evaluation_refs: list[str] = Field(default_factory=list)
    counterfactual_refs: list[str] = Field(default_factory=list)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class DecisionRecommendation(BaseModel):
    """Complete recommendation packet for one decision frame."""

    model_config = ConfigDict(extra="forbid")

    decision_frame: DecisionFrame
    options: list[DecisionOption]
    evaluations: list[OptionEvaluation]
    tradeoff_matrix: TradeoffMatrix | None
    counterfactuals: list[CounterfactualRun]
    recommended_option_id: str | None
    constraints: list[str]
    explanation: str
    created_at: datetime


def generic_balanced_weights() -> dict[str, float]:
    """Return the built-in domain-neutral balanced profile weights."""
    return {
        "goal_alignment": 0.18,
        "evidence_support": 0.14,
        "belief_confidence": 0.12,
        "risk_reduction": 0.16,
        "policy_allowance": 0.10,
        "autonomy_allowance": 0.10,
        "reversibility": 0.07,
        "cost_efficiency": 0.05,
        "urgency": 0.04,
        "uncertainty_reduction": 0.04,
    }


def _contains_domain_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in DOMAIN_UTILITY_TERMS)


__all__ = [
    "DecisionEvaluationRequest",
    "DecisionFrame",
    "DecisionFrameCreateRequest",
    "DecisionOption",
    "DecisionOptionCreateRequest",
    "DecisionRecommendation",
    "DecisionRecord",
    "DecisionRecordRequest",
    "OptionEvaluation",
    "TradeoffMatrix",
    "UtilityProfile",
    "UtilityProfileCreateRequest",
    "generic_balanced_weights",
]
