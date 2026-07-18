"""Read-only self-improvement observations from existing evaluation signals."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now

EXPERIMENT_AUTHORIZATION_TRANSACTION_ID = "AION-169-SI-0003"
EXPERIMENT_IMPLEMENTATION_TASK = "AION-170"
EXPERIMENT_AUTHORIZATION_SCOPE = "self-improvement-proposal-and-experiment-engine"

ObservationSourceType = Literal[
    "evaluation",
    "learning_signal",
    "learning_pattern",
    "experience",
    "lesson",
    "skill_candidate",
]

LOW_SCORE_THRESHOLD = 0.75


class ImprovementObservation(BaseModel):
    """One immutable observation that can seed a bounded improvement proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    observation_id: str = Field(min_length=1)
    source_type: ObservationSourceType
    source_ref: str = Field(min_length=1)
    trace_id: str | None = None
    problem_statement: str = Field(min_length=1)
    score_name: str | None = None
    observed_score: float | None = Field(default=None, ge=0.0, le=1.0)
    target_score: float | None = Field(default=None, ge=0.0, le=1.0)
    repeated_count: int = Field(default=1, ge=1)
    source_evidence_refs: tuple[str, ...] = Field(min_length=1)
    lessons: tuple[str, ...] = Field(default_factory=tuple)
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator(
        "observation_id",
        "source_ref",
        "problem_statement",
        "score_name",
        "trace_id",
    )
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "self-improvement observation text")
        return cleaned

    @field_validator("source_evidence_refs", "lessons")
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement observation reference")
        return cleaned

    @model_validator(mode="after")
    def observation_must_be_side_effect_free(self) -> ImprovementObservation:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("observation must use the AION-169 experiment authorization")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError("observations cannot modify source, Git, PRs, or runtime state")
        if self.observed_score is not None and self.target_score is not None:
            if self.observed_score >= self.target_score:
                raise ValueError("observed_score must be below target_score for failure intake")
        return self


def observation_from_evaluation_record(
    record: EvaluationRecord,
    *,
    observation_id: str | None = None,
    threshold: float = LOW_SCORE_THRESHOLD,
    repeated_count: int = 1,
) -> ImprovementObservation:
    """Create a read-only observation from the weakest deterministic evaluation score."""

    score_name, observed_score = _weakest_score(record)
    target_score = max(threshold, observed_score)
    if observed_score >= target_score:
        target_score = min(1.0, observed_score + 0.01)
    return ImprovementObservation(
        observation_id=observation_id or f"observation-{record.evaluation_id}",
        source_type="evaluation",
        source_ref=record.evaluation_id,
        trace_id=record.trace_id,
        problem_statement=(
            f"Evaluation {record.evaluation_id} scored {observed_score:.2f} "
            f"for {score_name}, below the target {target_score:.2f}."
        ),
        score_name=score_name,
        observed_score=observed_score,
        target_score=target_score,
        repeated_count=repeated_count,
        source_evidence_refs=(f"evaluation:{record.evaluation_id}:trace:{record.trace_id}",),
        lessons=tuple(record.lessons),
        created_at=utc_now(),
    )


def _weakest_score(record: EvaluationRecord) -> tuple[str, float]:
    if not record.scores:
        return "unscored_evaluation", 0.0
    return min(sorted(record.scores.items()), key=lambda item: item[1])


__all__ = [
    "EXPERIMENT_AUTHORIZATION_SCOPE",
    "EXPERIMENT_AUTHORIZATION_TRANSACTION_ID",
    "EXPERIMENT_IMPLEMENTATION_TASK",
    "ImprovementObservation",
    "LOW_SCORE_THRESHOLD",
    "ObservationSourceType",
    "observation_from_evaluation_record",
]
