"""Skill registry contracts owned by AION Brain."""

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.goals import LifecycleRiskLevel

SkillProcedureAction = Literal[
    "retrieve_context",
    "compile_context",
    "reason",
    "create_plan",
    "policy_check",
    "dry_run_execute",
    "evaluate_result",
    "record_learning",
    "ask_clarifying_question",
]
SkillCandidateStatus = Literal["candidate", "under_review", "approved", "rejected", "promoted"]
SkillStatus = Literal["draft", "active", "disabled", "archived"]
SkillActivationEventType = Literal[
    "skill_promoted",
    "skill_activated",
    "skill_disabled",
    "skill_archived",
]

FORBIDDEN_DOMAIN_TERMS = {
    "finance",
    "trading",
    "trade",
    "stock",
    "investment",
    "legal",
    "healthcare",
    "health",
    "medical",
    "hr",
    "procurement",
    "payroll",
}


class SkillProcedureStep(BaseModel):
    """One data-only procedural memory step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    action_type: SkillProcedureAction
    description: str = Field(min_length=1)
    capability_required: str | None = None
    input_template: dict[str, Any] = Field(default_factory=dict)
    expected_output: dict[str, Any] = Field(default_factory=dict)
    risk_level: LifecycleRiskLevel
    policy_action: str | None = None

    @field_validator("description")
    @classmethod
    def description_must_be_generic(cls, value: str) -> str:
        """Reject domain-specific step descriptions."""
        _reject_domain_terms(value, "description")
        return value


class SkillCandidate(BaseModel):
    """Controlled procedural learning candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    reflection_id: str | None = None
    source_trace_ids: list[str] = Field(default_factory=list)
    source_task_ids: list[str] = Field(default_factory=list)
    source_learning_signal_ids: list[str] = Field(default_factory=list)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    trigger_patterns: list[str] = Field(min_length=1)
    preconditions: list[str] = Field(default_factory=list)
    procedure_steps: list[SkillProcedureStep] = Field(min_length=1)
    expected_outcomes: list[str] = Field(default_factory=list)
    risk_level: LifecycleRiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    evaluation_summary: dict[str, Any] = Field(default_factory=dict)
    status: SkillCandidateStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_generic(cls, value: str) -> str:
        """Reject blank or domain-specific skill text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms(value, "skill text")
        return value

    @field_validator("trigger_patterns")
    @classmethod
    def triggers_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject domain-specific trigger patterns."""
        for pattern in value:
            _reject_domain_terms(pattern, "trigger_patterns")
        return value


class SkillRecord(BaseModel):
    """Active or draft procedural memory skill stored as data."""

    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(min_length=1)
    candidate_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: SkillStatus
    risk_level: LifecycleRiskLevel
    current_version: int = Field(ge=1)
    trigger_patterns: list[str] = Field(min_length=1)
    preconditions: list[str] = Field(default_factory=list)
    procedure_steps: list[SkillProcedureStep] = Field(min_length=1)
    expected_outcomes: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    activated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_generic(cls, value: str) -> str:
        """Reject domain-specific skill text."""
        _reject_domain_terms(value, "skill text")
        return value


class SkillVersion(BaseModel):
    """Immutable skill version data."""

    model_config = ConfigDict(extra="forbid")

    skill_version_id: str = Field(min_length=1)
    skill_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    trigger_patterns: list[str] = Field(min_length=1)
    preconditions: list[str] = Field(default_factory=list)
    procedure_steps: list[SkillProcedureStep] = Field(min_length=1)
    expected_outcomes: list[str] = Field(default_factory=list)
    change_reason: str = Field(min_length=1)
    source_candidate_id: str | None = None
    created_at: datetime | None = None


class SkillPromotionRequest(BaseModel):
    """Request to promote an approved skill candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    actor_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    activate: bool = False
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillPromotionResponse(BaseModel):
    """Promotion result."""

    model_config = ConfigDict(extra="forbid")

    promoted: bool
    skill_id: str | None
    skill_version_id: str | None
    candidate_id: str
    status: str
    reason: str | None = None


class SkillActivationRequest(BaseModel):
    """Request to transition a skill status."""

    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(min_length=1)
    to_status: SkillStatus
    actor_id: str | None = None
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillMatchRequest(BaseModel):
    """Request to match active procedural skills."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    risk_levels: list[LifecycleRiskLevel] = Field(default_factory=list)


class SkillMatchResult(BaseModel):
    """Deterministic skill match result."""

    model_config = ConfigDict(extra="forbid")

    skill: SkillRecord
    score: float = Field(ge=0.0, le=1.0)
    matched_patterns: list[str]
    reason: str


class SkillActivationEvent(BaseModel):
    """Audit event for skill activation status changes."""

    model_config = ConfigDict(extra="forbid")

    activation_event_id: str = Field(min_length=1)
    skill_id: str = Field(min_length=1)
    skill_version_id: str | None = None
    trace_id: str | None = None
    event_type: SkillActivationEventType
    from_status: str | None = None
    to_status: str | None = None
    reason: str | None = None
    actor_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


def _reject_domain_terms(value: str, field_name: str) -> None:
    normalized = set(re.findall(r"[a-z0-9]+", value.lower()))
    for term in FORBIDDEN_DOMAIN_TERMS:
        if term in normalized:
            raise ValueError(f"{field_name} contains domain-specific term: {term}")
