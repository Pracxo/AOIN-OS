"""Learning synthesis contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.concepts import reject_secret_like_keys
from aion_brain.contracts.experience import ExperienceRecord

LearningPatternType = Literal[
    "repeated_success",
    "repeated_failure",
    "recurring_block",
    "approval_bottleneck",
    "missing_context",
    "missing_effect",
    "unexpected_effect",
    "regression_drift",
    "replay_drift",
    "contradiction",
    "recovery_pattern",
    "generic",
]
LearningRecordStatus = Literal["active", "archived", "dismissed"]
LearningSeverity = Literal["low", "medium", "high", "critical"]
LessonType = Literal[
    "procedural",
    "contextual",
    "policy",
    "risk",
    "approval",
    "retrieval",
    "planning",
    "execution",
    "memory",
    "regression",
    "operator",
    "generic",
]
PatternMiningStatus = Literal["completed", "dry_run", "failed", "blocked_by_policy"]
LearningSynthesisMode = Literal["dry_run", "controlled"]
LearningSynthesisStatus = Literal[
    "completed",
    "dry_run",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
]
MiningType = Literal[
    "generic",
    "outcome",
    "command",
    "workflow",
    "regression",
    "replay",
    "approval",
    "operator",
]
SuggestionStatus = Literal["suggested", "accepted", "rejected", "converted", "archived"]
ProposedSkillType = Literal[
    "procedural",
    "retrieval",
    "planning",
    "execution",
    "review",
    "operator",
    "generic",
]


class LearningPattern(BaseModel):
    """A deterministic repeated learning pattern candidate."""

    model_config = ConfigDict(extra="forbid")

    pattern_id: str = Field(min_length=1)
    trace_id: str | None = None
    pattern_type: LearningPatternType
    status: LearningRecordStatus
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    experience_refs: list[str] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    frequency: int = Field(ge=1)
    confidence: float = Field(ge=0.0, le=1.0)
    severity: LearningSeverity
    recommendation: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class LessonRecord(BaseModel):
    """Generic lesson synthesized from learning patterns."""

    model_config = ConfigDict(extra="forbid")

    lesson_id: str = Field(min_length=1)
    trace_id: str | None = None
    lesson_type: LessonType
    status: LearningRecordStatus
    title: str = Field(min_length=1)
    lesson: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    pattern_refs: list[str] = Field(default_factory=list)
    experience_refs: list[str] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    applicability: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("applicability", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class PatternMiningRequest(BaseModel):
    """Request deterministic pattern mining."""

    model_config = ConfigDict(extra="forbid")

    pattern_mining_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    mining_type: MiningType = "generic"
    experience_ids: list[str] = Field(default_factory=list)
    experience_types: list[str] = Field(default_factory=list)
    min_frequency: int = Field(default=2, ge=2, le=100)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    limit: int = Field(default=500, ge=1, le=5000)
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class PatternMiningRun(BaseModel):
    """Result of deterministic pattern mining."""

    model_config = ConfigDict(extra="forbid")

    pattern_mining_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: PatternMiningStatus
    owner_scope: list[str] = Field(min_length=1)
    mining_type: MiningType
    input_experience_ids: list[str] = Field(default_factory=list)
    patterns: list[LearningPattern] = Field(default_factory=list)
    skipped: int = Field(ge=0)
    failed: int = Field(ge=0)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("result")
    @classmethod
    def result_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SkillCandidateSuggestion(BaseModel):
    """Reviewable suggestion to create a skill candidate later."""

    model_config = ConfigDict(extra="forbid")

    suggestion_id: str = Field(min_length=1)
    trace_id: str | None = None
    pattern_id: str | None = None
    lesson_id: str | None = None
    status: SuggestionStatus = "suggested"
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    proposed_skill_type: ProposedSkillType
    source_refs: list[str] = Field(default_factory=list)
    risk_level: LearningSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    promotion_allowed: bool = False
    skill_candidate_id: str | None = None
    approval_request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("promotion_allowed")
    @classmethod
    def promotion_default_must_stay_false(cls, value: bool) -> bool:
        if value:
            raise ValueError("promotion_allowed must remain false in v0.1")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class RegressionCandidateSuggestion(BaseModel):
    """Reviewable suggestion to create a regression case later."""

    model_config = ConfigDict(extra="forbid")

    regression_suggestion_id: str = Field(min_length=1)
    trace_id: str | None = None
    pattern_id: str | None = None
    outcome_id: str | None = None
    status: SuggestionStatus = "suggested"
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    severity: LearningSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    regression_case_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class LearningSynthesisRequest(BaseModel):
    """Request a deterministic learning synthesis run."""

    model_config = ConfigDict(extra="forbid")

    synthesis_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: LearningSynthesisMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    source_types: list[str] = Field(default_factory=list)
    outcome_ids: list[str] = Field(default_factory=list)
    experience_ids: list[str] = Field(default_factory=list)
    pattern_ids: list[str] = Field(default_factory=list)
    create_reflection_candidates: bool = False
    create_skill_suggestions: bool = False
    create_regression_suggestions: bool = False
    create_lessons: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class LearningSynthesisRun(BaseModel):
    """Result of a deterministic learning synthesis run."""

    model_config = ConfigDict(extra="forbid")

    synthesis_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: LearningSynthesisStatus
    mode: LearningSynthesisMode
    owner_scope: list[str] = Field(min_length=1)
    input_refs: list[str] = Field(default_factory=list)
    experiences: list[ExperienceRecord] = Field(default_factory=list)
    patterns: list[LearningPattern] = Field(default_factory=list)
    lessons: list[LessonRecord] = Field(default_factory=list)
    reflection_candidate_ids: list[str] = Field(default_factory=list)
    skill_candidate_suggestions: list[SkillCandidateSuggestion] = Field(default_factory=list)
    regression_candidate_suggestions: list[RegressionCandidateSuggestion] = Field(
        default_factory=list
    )
    result: dict[str, Any] = Field(default_factory=dict)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("result", "warnings")
    @classmethod
    def result_payloads_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_keys(value)
        return value


class ExperienceQueryResult(BaseModel):
    """Learning query result bundle."""

    model_config = ConfigDict(extra="forbid")

    experiences: list[ExperienceRecord] = Field(default_factory=list)
    patterns: list[LearningPattern] = Field(default_factory=list)
    lessons: list[LessonRecord] = Field(default_factory=list)
    skill_suggestions: list[SkillCandidateSuggestion] = Field(default_factory=list)
    regression_suggestions: list[RegressionCandidateSuggestion] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ExperienceQueryResult",
    "LearningPattern",
    "LearningPatternType",
    "LearningRecordStatus",
    "LearningSeverity",
    "LearningSynthesisMode",
    "LearningSynthesisRequest",
    "LearningSynthesisRun",
    "LearningSynthesisStatus",
    "LessonRecord",
    "LessonType",
    "MiningType",
    "PatternMiningRequest",
    "PatternMiningRun",
    "PatternMiningStatus",
    "ProposedSkillType",
    "RegressionCandidateSuggestion",
    "SkillCandidateSuggestion",
    "SuggestionStatus",
]
