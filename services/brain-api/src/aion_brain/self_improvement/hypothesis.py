"""Hypothesis generation contracts for the AION-170 experiment engine."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.observation import EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
from aion_brain.self_improvement.pattern_intake import ImprovementFailurePattern

ImprovementChangeType = Literal[
    "retrieval_ranking",
    "planning_policy",
    "regression_test",
    "procedural_skill_candidate",
    "prompt_policy",
    "generic",
]
MetricDirection = Literal["increase", "decrease"]


class ImprovementHypothesis(BaseModel):
    """Bounded hypothesis derived from a repeated failure pattern."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    hypothesis_id: str = Field(min_length=1)
    failure_pattern_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    change_type: ImprovementChangeType
    target_metric: str = Field(min_length=1)
    target_direction: MetricDirection
    target_delta: float = Field(gt=0.0, le=1.0)
    allowed_paths: tuple[str, ...] = Field(min_length=1)
    prohibited_paths: tuple[str, ...] = Field(min_length=1)
    source_evidence_refs: tuple[str, ...] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    generated_by: str = Field(min_length=1)
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator(
        "hypothesis_id",
        "failure_pattern_id",
        "statement",
        "target_metric",
        "generated_by",
    )
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "self-improvement hypothesis text")
        return cleaned

    @field_validator("allowed_paths", "prohibited_paths", "source_evidence_refs")
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip().replace("\\", "/") for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement hypothesis reference")
        return cleaned

    @model_validator(mode="after")
    def hypothesis_must_be_bounded_and_side_effect_free(self) -> ImprovementHypothesis:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("hypothesis must use the AION-169 experiment authorization")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError("hypotheses cannot modify source, Git, PRs, or runtime state")
        overlap = set(self.allowed_paths) & set(self.prohibited_paths)
        if overlap:
            raise ValueError(f"allowed paths overlap prohibited paths: {sorted(overlap)}")
        return self


class HypothesisGenerator(Protocol):
    """Protocol for explicitly configured hypothesis generators."""

    generator_id: str

    def generate(self, pattern: ImprovementFailurePattern) -> ImprovementHypothesis:
        """Generate one bounded hypothesis."""


class DisabledHypothesisGenerator:
    """Fail-closed runtime default; no autonomous hypothesis generation."""

    generator_id = "disabled-hypothesis-generator"

    def generate(self, pattern: ImprovementFailurePattern) -> ImprovementHypothesis:  # noqa: ARG002
        raise RuntimeError("self-improvement hypothesis generation is disabled")


class DeterministicTestHypothesisGenerator:
    """Deterministic test double for focused proposal-engine tests."""

    generator_id = "deterministic-test-hypothesis-generator"

    def __init__(
        self,
        *,
        allowed_paths: tuple[str, ...] = (
            "services/brain-api/tests/fixtures/self_improvement/",
        ),
        prohibited_paths: tuple[str, ...] = (
            ".github/",
            "docs/self-improvement/holdout/",
            "services/brain-api/src/aion_brain/self_improvement/approval.py",
            "services/brain-api/src/aion_brain/self_improvement/protected_paths.py",
        ),
    ) -> None:
        self._allowed_paths = allowed_paths
        self._prohibited_paths = prohibited_paths

    def generate(self, pattern: ImprovementFailurePattern) -> ImprovementHypothesis:
        change_type = _change_type_for(pattern)
        target_metric, direction = _metric_for(pattern)
        return ImprovementHypothesis(
            hypothesis_id=f"hypothesis-{pattern.failure_pattern_id}",
            failure_pattern_id=pattern.failure_pattern_id,
            statement=(
                f"Improve {target_metric} for {pattern.pattern_key} using a bounded "
                f"{change_type.replace('_', ' ')} change."
            ),
            change_type=change_type,
            target_metric=target_metric,
            target_direction=direction,
            target_delta=0.05,
            allowed_paths=self._allowed_paths,
            prohibited_paths=self._prohibited_paths,
            source_evidence_refs=pattern.source_evidence_refs,
            confidence=pattern.confidence,
            generated_by=self.generator_id,
            created_at=utc_now(),
        )


def _change_type_for(pattern: ImprovementFailurePattern) -> ImprovementChangeType:
    if pattern.pattern_type == "retrieval_failure":
        return "retrieval_ranking"
    if pattern.pattern_type == "planning_failure":
        return "planning_policy"
    if pattern.pattern_type in {"regression_drift", "replay_drift"}:
        return "regression_test"
    if pattern.pattern_type == "evidence_grounding_failure":
        return "prompt_policy"
    return "generic"


def _metric_for(pattern: ImprovementFailurePattern) -> tuple[str, MetricDirection]:
    if pattern.pattern_type == "retrieval_failure":
        return "retrieval_precision", "increase"
    if pattern.pattern_type == "planning_failure":
        return "plan_success", "increase"
    if pattern.pattern_type == "evidence_grounding_failure":
        return "evidence_grounding", "increase"
    if pattern.pattern_type in {"regression_drift", "replay_drift"}:
        return "regression_count", "decrease"
    return "task_success", "increase"


__all__ = [
    "DeterministicTestHypothesisGenerator",
    "DisabledHypothesisGenerator",
    "HypothesisGenerator",
    "ImprovementChangeType",
    "ImprovementHypothesis",
    "MetricDirection",
]
