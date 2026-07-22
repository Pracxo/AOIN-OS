"""Governed continual-learning contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.cognitive_state import (
    FrozenDict,
    fingerprint_model,
    fingerprint_payload,
    freeze_payload,
)
from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

SCHEMA_VERSION = "continual-learning/v1"
CANONICALIZATION_VERSION = "continual-learning-canonical-json/v1"
AUTHORIZATION_ID = "AION-195-CA-0007"
IMPLEMENTATION_TASK = "AION-196"

CandidateType = Literal[
    "memory",
    "retrieval_policy",
    "planning_policy",
    "procedural_skill",
    "world_model_adapter",
    "strategy",
]
PromotionStatus = Literal[
    "blocked",
    "operator_review_required",
    "approved_by_external_governance",
]
RiskLevel = Literal["low", "medium", "high", "critical"]

SAFE_REFERENCE_PREFIXES = (
    "aion://",
    "memory://",
    "evidence://",
    "policy://",
    "baseline://",
    "holdout://",
    "rollback://",
    "operator-approved://",
    "synthetic://",
)
BLOCKED_REFERENCE_PREFIXES = (
    "http:",
    "https:",
    "ftp:",
    "file:",
    "s3:",
    "gs:",
)


def validate_learning_reference(value: str, field_name: str) -> str:
    """Validate an opaque governed-learning reference."""

    reject_hidden_or_secret_text(value, field_name)
    stripped = value.strip()
    lowered = stripped.lower()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    if lowered.startswith(BLOCKED_REFERENCE_PREFIXES):
        raise ValueError(f"{field_name} must not be an arbitrary external location")
    if stripped.startswith(("/", "~")):
        raise ValueError(f"{field_name} must not be an implicit filesystem location")
    if "../" in stripped or "..\\" in stripped:
        raise ValueError(f"{field_name} must not contain traversal")
    if "://" in stripped and not lowered.startswith(SAFE_REFERENCE_PREFIXES):
        raise ValueError(f"{field_name} must use an approved opaque reference prefix")
    if lowered.startswith(".git") or "/.git" in lowered:
        raise ValueError(f"{field_name} must not target repository internals")
    return stripped


class ContinualLearningModel(BaseModel):
    """Base model for immutable continual-learning contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class ContinualLearningFingerprintedModel(ContinualLearningModel):
    """Immutable model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical continual-learning payload")
        return self


class ContinualLearningRuntimeBoundary(ContinualLearningFingerprintedModel):
    """False-by-default runtime boundary for governed-learning records."""

    runtime_effect: bool = False
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    model_weight_training: int = Field(default=0, ge=0)
    model_weights_changed: bool = False
    source_mutation: bool = False
    git_mutation: bool = False
    background_loop: bool = False
    automatic_promotion: bool = False
    unauthorized_promotion_count: int = Field(default=0, ge=0)
    self_approval_count: int = Field(default=0, ge=0)
    holdout_leakage_count: int = Field(default=0, ge=0)
    production_exposure: bool = False

    @model_validator(mode="after")
    def runtime_boundaries_must_remain_disabled(self) -> Self:
        for key in (
            "runtime_effect",
            "model_weights_changed",
            "source_mutation",
            "git_mutation",
            "background_loop",
            "automatic_promotion",
            "production_exposure",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        for key in (
            "network_calls",
            "connector_calls",
            "model_provider_calls",
            "model_weight_training",
            "unauthorized_promotion_count",
            "self_approval_count",
            "holdout_leakage_count",
        ):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class ContinualLearningObservation(ContinualLearningRuntimeBoundary):
    """One local observation that can be grouped into a learning episode."""

    observation_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    signal_tags: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("observation_id", "source", "summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "continual-learning observation text")
        return value.strip()

    @field_validator("signal_tags", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                dict.fromkeys(
                    validate_learning_reference(item, "continual-learning observation ref")
                    for item in value
                    if item.strip()
                )
            )
        )

    @field_validator("metadata", mode="after")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "continual-learning metadata key")
            if isinstance(nested, str):
                reject_hidden_or_secret_text(nested, "continual-learning metadata value")
        return cast(FrozenDict, freeze_payload(value))


class LearningEpisode(ContinualLearningRuntimeBoundary):
    """Immutable episode used for replay or protected holdout evaluation."""

    episode_id: str = Field(min_length=1)
    observations: tuple[ContinualLearningObservation, ...]
    outcome_label: str = Field(min_length=1)
    baseline_ref: str = Field(min_length=1)
    policy_ref: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    protected_holdout: bool = False
    allowed_for_replay: bool = True
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    max_observations: int = Field(default=20, ge=1)

    @field_validator("episode_id", "outcome_label", "baseline_ref", "policy_ref")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return validate_learning_reference(value, "learning episode text")

    @field_validator("evidence_refs")
    @classmethod
    def evidence_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                dict.fromkeys(
                    validate_learning_reference(item, "learning episode ref")
                    for item in value
                    if item.strip()
                )
            )
        )

    @model_validator(mode="after")
    def episode_must_preserve_holdout(self) -> Self:
        if not self.observations:
            raise ValueError("learning episode requires observations")
        if len(self.observations) > self.max_observations:
            raise ValueError("learning episode exceeds max_observations")
        observation_ids = [item.observation_id for item in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("learning episode observations must be unique")
        if self.protected_holdout and self.allowed_for_replay:
            raise ValueError("protected holdout episodes must be excluded from replay")
        return self


class ReplaySample(ContinualLearningRuntimeBoundary):
    """Deterministic replay sample that excludes protected holdout episodes."""

    sample_id: str = Field(min_length=1)
    episode_ids: tuple[str, ...]
    excluded_holdout_episode_ids: tuple[str, ...] = Field(default_factory=tuple)
    baseline_ref: str = Field(min_length=1)
    policy_ref: str = Field(min_length=1)
    max_episodes: int = Field(ge=1)
    deterministic_replay_hash: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("sample_id", "baseline_ref", "policy_ref")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return validate_learning_reference(value, "replay sample text")

    @field_validator("episode_ids", "excluded_holdout_episode_ids")
    @classmethod
    def ids_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            validate_learning_reference(item, "replay sample episode id")
            for item in value
            if item.strip()
        )

    @model_validator(mode="after")
    def sample_must_be_deterministic_and_holdout_safe(self) -> Self:
        if not self.episode_ids:
            raise ValueError("replay sample requires episode ids")
        if len(self.episode_ids) > self.max_episodes:
            raise ValueError("replay sample exceeds max_episodes")
        if len(self.episode_ids) != len(set(self.episode_ids)):
            raise ValueError("replay sample episode ids must be unique")
        overlap = set(self.episode_ids) & set(self.excluded_holdout_episode_ids)
        if overlap:
            raise ValueError("replay sample must exclude protected holdout episodes")
        expected = fingerprint_payload(
            {
                "sample_id": self.sample_id,
                "episode_ids": self.episode_ids,
                "excluded_holdout_episode_ids": self.excluded_holdout_episode_ids,
                "baseline_ref": self.baseline_ref,
                "policy_ref": self.policy_ref,
                "max_episodes": self.max_episodes,
            }
        )
        if self.deterministic_replay_hash is None:
            object.__setattr__(self, "deterministic_replay_hash", expected)
        elif self.deterministic_replay_hash != expected:
            raise ValueError("deterministic_replay_hash must match replay sample payload")
        object.__setattr__(self, "fingerprint", fingerprint_model(self, exclude={"fingerprint"}))
        return self


class LearningCandidate(ContinualLearningRuntimeBoundary):
    """Base isolated candidate produced from replay, never promoted automatically."""

    candidate_id: str = Field(min_length=1)
    candidate_type: CandidateType
    version: int = Field(default=1, ge=1)
    baseline_ref: str = Field(min_length=1)
    replay_sample_id: str = Field(min_length=1)
    source_episode_ids: tuple[str, ...]
    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...]
    operator_review_required: bool = True
    candidate_isolated: bool = True
    promotion_requested: bool = False
    promotion_allowed: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("candidate_id", "baseline_ref", "replay_sample_id", "summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return validate_learning_reference(value, "learning candidate text")

    @field_validator("source_episode_ids", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                dict.fromkeys(
                    validate_learning_reference(item, "learning candidate ref")
                    for item in value
                    if item.strip()
                )
            )
        )

    @model_validator(mode="after")
    def candidate_must_remain_isolated_and_review_gated(self) -> Self:
        if not self.source_episode_ids:
            raise ValueError("learning candidate requires source episodes")
        if not self.evidence_refs:
            raise ValueError("learning candidate requires evidence refs")
        if not self.operator_review_required:
            raise ValueError("operator review is required")
        if not self.candidate_isolated:
            raise ValueError("candidate isolation is required")
        if self.promotion_requested or self.promotion_allowed:
            raise ValueError("AION-196 must not request or allow promotion by default")
        return self


class RetrievalPolicyCandidate(LearningCandidate):
    """Candidate retrieval-ranking policy derived from replay evidence."""

    candidate_type: Literal["retrieval_policy"] = "retrieval_policy"
    query_policy: str = Field(min_length=1)
    ranking_rule: str = Field(min_length=1)
    allowed_source_refs: tuple[str, ...]

    @field_validator("query_policy", "ranking_rule")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "retrieval policy candidate text")
        return value.strip()

    @field_validator("allowed_source_refs")
    @classmethod
    def source_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                dict.fromkeys(
                    validate_learning_reference(item, "retrieval policy source ref")
                    for item in value
                    if item.strip()
                )
            )
        )

    @model_validator(mode="after")
    def retrieval_policy_requires_sources(self) -> Self:
        if not self.allowed_source_refs:
            raise ValueError("retrieval policy candidates require allowed sources")
        return self


class PlanningPolicyCandidate(LearningCandidate):
    """Candidate planning heuristic derived from replay outcomes."""

    candidate_type: Literal["planning_policy"] = "planning_policy"
    planning_rule: str = Field(min_length=1)
    budget_policy: str = Field(min_length=1)
    replanning_trigger: str = Field(min_length=1)

    @field_validator("planning_rule", "budget_policy", "replanning_trigger")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "planning policy candidate text")
        return value.strip()


class ProceduralSkillCandidate(LearningCandidate):
    """Candidate procedure captured for operator review only."""

    candidate_type: Literal["procedural_skill"] = "procedural_skill"
    skill_name: str = Field(min_length=1)
    steps: tuple[str, ...]
    preconditions: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("skill_name")
    @classmethod
    def skill_name_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "procedural skill candidate text")
        return value.strip()

    @field_validator("steps", "preconditions")
    @classmethod
    def procedural_text_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "procedural skill candidate text")
        return tuple(item.strip() for item in value if item.strip())

    @model_validator(mode="after")
    def procedure_requires_steps(self) -> Self:
        if not self.steps:
            raise ValueError("procedural skill candidates require steps")
        return self


class WorldModelAdapterCandidate(LearningCandidate):
    """Candidate adapter for local world-model prediction behavior."""

    candidate_type: Literal["world_model_adapter"] = "world_model_adapter"
    adapter_name: str = Field(min_length=1)
    predicted_transition: str = Field(min_length=1)
    uncertainty_delta: float = Field(ge=0.0, le=1.0)

    @field_validator("adapter_name", "predicted_transition")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "world-model adapter candidate text")
        return value.strip()


class StrategyCandidate(LearningCandidate):
    """Candidate strategy-selection rule derived from replay outcomes."""

    candidate_type: Literal["strategy"] = "strategy"
    strategy_name: str = Field(min_length=1)
    selection_rule: str = Field(min_length=1)
    expected_goal_progress: float = Field(ge=0.0, le=1.0)

    @field_validator("strategy_name", "selection_rule")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "strategy candidate text")
        return value.strip()


class ForgettingRisk(ContinualLearningRuntimeBoundary):
    """Candidate-level catastrophic-forgetting and holdout risk result."""

    risk_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    baseline_ref: str = Field(min_length=1)
    protected_holdout_score: float = Field(ge=0.0, le=1.0)
    baseline_regression_rate: float = Field(ge=0.0, le=1.0)
    contradiction_loss_rate: float = Field(ge=0.0, le=1.0)
    catastrophic_forgetting_detected: bool = False
    risk_level: RiskLevel = "low"
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("risk_id", "candidate_id", "baseline_ref")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return validate_learning_reference(value, "forgetting risk text")

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                dict.fromkeys(
                    validate_learning_reference(item, "forgetting risk ref")
                    for item in value
                    if item.strip()
                )
            )
        )

    @model_validator(mode="after")
    def risk_level_must_match_forgetting_signal(self) -> Self:
        unsafe = (
            self.protected_holdout_score < 0.95
            or self.baseline_regression_rate > 0.05
            or self.contradiction_loss_rate > 0.0
        )
        if unsafe and not self.catastrophic_forgetting_detected:
            raise ValueError("unsafe forgetting risk must be explicit")
        if self.catastrophic_forgetting_detected and self.risk_level == "low":
            raise ValueError("catastrophic forgetting cannot be low risk")
        return self


class LearningEvaluation(ContinualLearningRuntimeBoundary):
    """Protected-holdout benchmark evaluation for one isolated candidate."""

    evaluation_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    candidate_version: int = Field(ge=1)
    replay_sample_id: str = Field(min_length=1)
    forgetting_risk: ForgettingRisk
    protected_holdout_score: float = Field(ge=0.0, le=1.0)
    baseline_regression_rate: float = Field(ge=0.0, le=1.0)
    deterministic_replay: bool = True
    candidate_isolation_verified: bool = True
    rollback_available: bool = True
    promotion_requires_approval: bool = True
    approved_for_promotion: bool = False
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("evaluation_id", "candidate_id", "replay_sample_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return validate_learning_reference(value, "learning evaluation text")

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                dict.fromkeys(
                    validate_learning_reference(item, "learning evaluation ref")
                    for item in value
                    if item.strip()
                )
            )
        )

    @model_validator(mode="after")
    def evaluation_must_pass_safety_floor(self) -> Self:
        if self.candidate_id != self.forgetting_risk.candidate_id:
            raise ValueError("evaluation candidate must match forgetting risk")
        if self.protected_holdout_score < 0.95:
            raise ValueError("protected holdout score is below safety floor")
        if self.baseline_regression_rate > 0.05:
            raise ValueError("baseline regression exceeds safety threshold")
        if self.forgetting_risk.catastrophic_forgetting_detected:
            raise ValueError("catastrophic forgetting blocks learning evaluation")
        for key in (
            "deterministic_replay",
            "candidate_isolation_verified",
            "rollback_available",
            "promotion_requires_approval",
        ):
            if not getattr(self, key):
                raise ValueError(f"{key} must be true")
        if self.approved_for_promotion:
            raise ValueError("AION-196 evaluations must not approve promotion")
        return self


class PromotionRequest(ContinualLearningRuntimeBoundary):
    """Approval-bound promotion request that never performs promotion."""

    request_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    candidate_version: int = Field(ge=1)
    evaluation_id: str = Field(min_length=1)
    requested_by: str = Field(min_length=1)
    status: PromotionStatus = "operator_review_required"
    approved_by: str | None = None
    approval_ref: str | None = None
    promotion_performed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "request_id",
        "candidate_id",
        "evaluation_id",
        "requested_by",
        "approved_by",
        "approval_ref",
    )
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_learning_reference(value, "promotion request text")

    @model_validator(mode="after")
    def promotion_request_must_be_approval_bound(self) -> Self:
        if self.promotion_performed:
            raise ValueError("promotion must not be performed")
        if self.status == "approved_by_external_governance":
            if not self.approved_by or not self.approval_ref:
                raise ValueError("approved promotion requires external governance evidence")
            if self.requested_by == self.approved_by:
                raise ValueError("self approval is prohibited")
        else:
            if self.approved_by or self.approval_ref:
                raise ValueError("approval evidence is only valid for approved status")
        return self


class LearningRollbackPlan(ContinualLearningRuntimeBoundary):
    """Rollback plan that restores the immutable baseline if promotion is rejected."""

    plan_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    candidate_version: int = Field(ge=1)
    baseline_ref: str = Field(min_length=1)
    rollback_steps: tuple[str, ...]
    rollback_available: bool = True
    source_restore_required: bool = False
    model_weight_restore_required: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("plan_id", "candidate_id", "baseline_ref")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return validate_learning_reference(value, "rollback plan text")

    @field_validator("rollback_steps")
    @classmethod
    def rollback_steps_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "rollback step")
        return tuple(item.strip() for item in value if item.strip())

    @model_validator(mode="after")
    def rollback_plan_must_restore_baseline_only(self) -> Self:
        if not self.rollback_steps:
            raise ValueError("rollback plan requires steps")
        if not self.rollback_available:
            raise ValueError("rollback must be available")
        if self.source_restore_required:
            raise ValueError("AION-196 rollback must not require source restore")
        if self.model_weight_restore_required:
            raise ValueError("AION-196 rollback must not require model weight restore")
        return self


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "SCHEMA_VERSION",
    "CandidateType",
    "ContinualLearningFingerprintedModel",
    "ContinualLearningModel",
    "ContinualLearningObservation",
    "ContinualLearningRuntimeBoundary",
    "ForgettingRisk",
    "LearningCandidate",
    "LearningEpisode",
    "LearningEvaluation",
    "LearningRollbackPlan",
    "PlanningPolicyCandidate",
    "PromotionRequest",
    "PromotionStatus",
    "ReplaySample",
    "RetrievalPolicyCandidate",
    "RiskLevel",
    "ProceduralSkillCandidate",
    "StrategyCandidate",
    "WorldModelAdapterCandidate",
    "fingerprint_payload",
    "validate_learning_reference",
]
