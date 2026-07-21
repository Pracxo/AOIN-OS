"""Predictive world-model contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Self, cast

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

SCHEMA_VERSION = "world-model/v1"
CANONICALIZATION_VERSION = "world-model-canonical-json/v1"
AUTHORIZATION_ID = "AION-185-CA-0002"
IMPLEMENTATION_TASK = "AION-186"

WorldFeatureValue = str | int | float | bool
EffectDirection = Literal["unchanged", "increased", "decreased", "changed", "added", "removed"]
ModelKind = Literal["deterministic-counts", "probabilistic-counts"]


class WorldModelBase(BaseModel):
    """Base model for immutable world-model contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class WorldModelFingerprintedModel(WorldModelBase):
    """Immutable model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical world-model payload")
        return self


class WorldState(WorldModelFingerprintedModel):
    """One bounded world state represented as deterministic features."""

    state_id: str = Field(min_length=1)
    features: dict[str, WorldFeatureValue] = Field(default_factory=dict)
    provenance_refs: tuple[str, ...] = Field(default_factory=tuple)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("state_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "world state id")
        return value.strip()

    @field_validator("features", mode="after")
    @classmethod
    def features_must_be_safe(
        cls,
        value: dict[str, WorldFeatureValue],
    ) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "world state feature key")
            if isinstance(nested, str):
                reject_hidden_or_secret_text(nested, "world state feature value")
        return cast(FrozenDict, freeze_payload(value))

    @field_validator("provenance_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "world state provenance ref")
        return value


class WorldObservation(WorldModelFingerprintedModel):
    """One observation that anchors a world state to provenance."""

    observation_id: str = Field(min_length=1)
    state: WorldState
    source: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("observation_id", "source")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "world observation text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "world observation evidence ref")
        return value


class WorldActionReference(WorldModelFingerprintedModel):
    """A referenced action whose effects may be predicted but not executed."""

    action_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    parameters: dict[str, WorldFeatureValue] = Field(default_factory=dict)
    reversible: bool = True
    irreversible_effect: bool = False
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("action_id", "name")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "world action text")
        return value.strip()

    @field_validator("parameters", mode="after")
    @classmethod
    def parameters_must_be_safe(
        cls,
        value: dict[str, WorldFeatureValue],
    ) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "world action parameter key")
            if isinstance(nested, str):
                reject_hidden_or_secret_text(nested, "world action parameter value")
        return cast(FrozenDict, freeze_payload(value))

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "world action evidence ref")
        return value

    @model_validator(mode="after")
    def irreversible_effect_must_match_reversibility(self) -> Self:
        if self.irreversible_effect and self.reversible:
            raise ValueError("irreversible_effect requires reversible=false")
        return self


class TransitionEvidence(WorldModelFingerprintedModel):
    """One observed state transition for a referenced action."""

    evidence_id: str = Field(min_length=1)
    source_state: WorldState
    action: WorldActionReference
    outcome_state: WorldState
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("evidence_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "transition evidence id")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "transition evidence ref")
        return value


class OutcomePrediction(WorldModelFingerprintedModel):
    """One possible future outcome for a transition prediction."""

    outcome_id: str = Field(min_length=1)
    state: WorldState
    probability: float = Field(ge=0.0, le=1.0)
    support_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    reversible_effect: bool
    irreversible_effect: bool
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("outcome_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "outcome prediction id")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "outcome evidence ref")
        return value

    @model_validator(mode="after")
    def irreversible_effect_must_match_reversibility(self) -> Self:
        if self.irreversible_effect and self.reversible_effect:
            raise ValueError("irreversible effects cannot also be reversible")
        return self


class UncertaintyEstimate(WorldModelFingerprintedModel):
    """Bounded uncertainty metadata for one predicted transition."""

    uncertainty_id: str = Field(min_length=1)
    source_state_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    sample_count: int = Field(ge=0)
    entropy: float = Field(ge=0.0)
    normalized_entropy: float = Field(ge=0.0, le=1.0)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    confidence_interval_low: float = Field(ge=0.0, le=1.0)
    confidence_interval_high: float = Field(ge=0.0, le=1.0)
    unknown_state: bool = False
    fail_closed: bool = False

    @field_validator("uncertainty_id", "source_state_id", "action_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "uncertainty estimate text")
        return value.strip()

    @model_validator(mode="after")
    def uncertainty_bounds_must_be_consistent(self) -> Self:
        if self.confidence_interval_low > self.confidence_interval_high:
            raise ValueError("confidence interval low cannot exceed high")
        if self.unknown_state and not self.fail_closed:
            raise ValueError("unknown states must fail closed")
        if self.fail_closed and self.sample_count != 0 and self.unknown_state:
            raise ValueError("unknown fail-closed predictions must have zero samples")
        return self


class TransitionPrediction(WorldModelFingerprintedModel):
    """Predicted distribution over next states for one action reference."""

    prediction_id: str = Field(min_length=1)
    source_state_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    model_kind: ModelKind
    model_version: str = Field(min_length=1)
    model_fingerprint: str = Field(min_length=64, max_length=64)
    outcomes: tuple[OutcomePrediction, ...] = Field(default_factory=tuple)
    uncertainty: UncertaintyEstimate
    probability_sum_error: float = Field(default=0.0, ge=0.0)
    unknown_state: bool = False
    fail_closed: bool = False
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "prediction_id",
        "source_state_id",
        "action_id",
        "model_version",
        "model_fingerprint",
    )
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "transition prediction text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "transition prediction ref")
        return value

    @model_validator(mode="after")
    def probability_distribution_must_be_bounded(self) -> Self:
        probability_sum = sum(outcome.probability for outcome in self.outcomes)
        expected_error = abs(1.0 - probability_sum) if self.outcomes else 0.0
        if abs(self.probability_sum_error - expected_error) > 1e-12:
            raise ValueError("probability_sum_error must match outcome probabilities")
        if self.unknown_state:
            if self.outcomes:
                raise ValueError("unknown-state predictions must not expose outcomes")
            if not self.fail_closed:
                raise ValueError("unknown-state predictions must fail closed")
        else:
            if not self.outcomes:
                raise ValueError("known-state predictions require at least one outcome")
            if expected_error > 1e-9:
                raise ValueError("outcome probabilities must sum to 1.0")
            if self.fail_closed:
                raise ValueError("known-state predictions must not fail closed")
        if self.uncertainty.unknown_state != self.unknown_state:
            raise ValueError("uncertainty unknown_state must match prediction")
        if self.uncertainty.fail_closed != self.fail_closed:
            raise ValueError("uncertainty fail_closed must match prediction")
        return self


class CausalHypothesis(WorldModelFingerprintedModel):
    """Explicit action-effect hypothesis derived from transition evidence."""

    hypothesis_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    cause_feature: str = Field(min_length=1)
    effect_feature: str = Field(min_length=1)
    direction: EffectDirection
    expected_effect: WorldFeatureValue | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    support_count: int = Field(ge=0)
    contradicting_count: int = Field(ge=0)
    reversible_effect: bool
    irreversible_effect: bool
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("hypothesis_id", "action_id", "cause_feature", "effect_feature")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "causal hypothesis text")
        return value.strip()

    @field_validator("expected_effect")
    @classmethod
    def expected_effect_must_be_safe(
        cls,
        value: WorldFeatureValue | None,
    ) -> WorldFeatureValue | None:
        if isinstance(value, str):
            reject_hidden_or_secret_text(value, "causal expected effect")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "causal hypothesis evidence ref")
        return value

    @model_validator(mode="after")
    def irreversible_effect_must_match_reversibility(self) -> Self:
        if self.irreversible_effect and self.reversible_effect:
            raise ValueError("irreversible effects cannot also be reversible")
        if self.support_count == 0 and self.confidence > 0.0:
            raise ValueError("unsupported hypotheses must have zero confidence")
        return self


class CounterfactualScenario(WorldModelFingerprintedModel):
    """Bounded action branch to roll forward without executing actions."""

    scenario_id: str = Field(min_length=1)
    start_state: WorldState
    actions: tuple[WorldActionReference, ...]
    max_depth: int = Field(ge=1, le=20)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("scenario_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "counterfactual scenario id")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "counterfactual scenario ref")
        return value

    @model_validator(mode="after")
    def action_depth_must_fit_limit(self) -> Self:
        if not self.actions:
            raise ValueError("counterfactual scenarios require at least one action")
        if len(self.actions) > self.max_depth:
            raise ValueError("counterfactual actions exceed max_depth")
        return self


class CounterfactualRollout(WorldModelFingerprintedModel):
    """Deterministic predictions for a counterfactual scenario."""

    rollout_id: str = Field(min_length=1)
    scenario: CounterfactualScenario
    predictions: tuple[TransitionPrediction, ...]
    terminal_distribution: tuple[OutcomePrediction, ...]
    replay_hash: str = Field(min_length=64, max_length=64)
    forbidden_side_effects: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("rollout_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "counterfactual rollout id")
        return value.strip()

    @model_validator(mode="after")
    def replay_hash_must_match_rollout(self) -> Self:
        if self.forbidden_side_effects != 0:
            raise ValueError("counterfactual rollouts must not create side effects")
        expected = fingerprint_payload(
            {
                "scenario": self.scenario,
                "predictions": self.predictions,
                "terminal_distribution": self.terminal_distribution,
            }
        )
        if self.replay_hash != expected:
            raise ValueError("replay_hash must match rollout payload")
        return self


class WorldModelSnapshot(WorldModelFingerprintedModel):
    """Deterministic snapshot of fitted transition evidence."""

    snapshot_id: str = Field(min_length=1)
    model_kind: ModelKind
    model_version: str = Field(min_length=1)
    evidence_count: int = Field(ge=0)
    state_count: int = Field(ge=0)
    action_count: int = Field(ge=0)
    transition_count: int = Field(ge=0)
    causal_hypotheses: tuple[CausalHypothesis, ...] = Field(default_factory=tuple)
    model_fingerprint: str = Field(min_length=64, max_length=64)
    runtime_effect: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    approval_created: bool = False
    merged: bool = False
    production_exposure: bool = False
    model_weights_changed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("snapshot_id", "model_version", "model_fingerprint")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "world-model snapshot text")
        return value.strip()

    @model_validator(mode="after")
    def runtime_flags_must_remain_false(self) -> Self:
        for key in (
            "runtime_effect",
            "source_modified",
            "git_mutated",
            "pull_request_created",
            "approval_created",
            "merged",
            "production_exposure",
            "model_weights_changed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        return self


class WorldModelEvaluation(WorldModelFingerprintedModel):
    """Evaluation metrics for the predictive world model."""

    evaluation_id: str = Field(min_length=1)
    evaluated_task: str = IMPLEMENTATION_TASK
    evaluation_name: str = "AION-PWME-001"
    model_version: str = Field(min_length=1)
    prediction_count: int = Field(ge=0)
    transition_top_1_accuracy: float = Field(ge=0.0, le=1.0)
    brier_score: float = Field(ge=0.0)
    probability_sum_error: float = Field(ge=0.0)
    unknown_state_fail_closed_rate: float = Field(ge=0.0, le=1.0)
    deterministic_replay_rate: float = Field(ge=0.0, le=1.0)
    forbidden_side_effects: int = Field(ge=0)
    runtime_effect: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    approval_created: bool = False
    merged: bool = False
    production_exposure: bool = False
    model_weights_changed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("evaluation_id", "evaluated_task", "evaluation_name", "model_version")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "world-model evaluation text")
        return value.strip()

    @model_validator(mode="after")
    def evaluation_must_not_report_side_effects(self) -> Self:
        for key in (
            "runtime_effect",
            "source_modified",
            "git_mutated",
            "pull_request_created",
            "approval_created",
            "merged",
            "production_exposure",
            "model_weights_changed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        if self.forbidden_side_effects != 0:
            raise ValueError("forbidden_side_effects must be zero")
        return self


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "SCHEMA_VERSION",
    "CausalHypothesis",
    "CounterfactualRollout",
    "CounterfactualScenario",
    "ModelKind",
    "OutcomePrediction",
    "TransitionEvidence",
    "TransitionPrediction",
    "UncertaintyEstimate",
    "WorldActionReference",
    "WorldFeatureValue",
    "WorldModelEvaluation",
    "WorldModelSnapshot",
    "WorldObservation",
    "WorldState",
    "fingerprint_model",
    "fingerprint_payload",
]
