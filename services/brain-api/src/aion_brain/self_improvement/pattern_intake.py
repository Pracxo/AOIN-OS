"""Repeated failure-pattern intake for governed self-improvement."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.experience import ExperienceRecord
from aion_brain.contracts.learning_synthesis import LearningPattern
from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.observation import (
    EXPERIMENT_AUTHORIZATION_TRANSACTION_ID,
    ImprovementObservation,
)

ImprovementFailurePatternType = Literal[
    "retrieval_failure",
    "planning_failure",
    "evidence_grounding_failure",
    "policy_block",
    "regression_drift",
    "replay_drift",
    "generic_failure",
]


class ImprovementFailurePattern(BaseModel):
    """A repeated failure pattern ready for bounded hypothesis generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    failure_pattern_id: str = Field(min_length=1)
    pattern_type: ImprovementFailurePatternType
    pattern_key: str = Field(min_length=1)
    problem_statement: str = Field(min_length=1)
    source_observation_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_learning_pattern_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_experience_ids: tuple[str, ...] = Field(default_factory=tuple)
    frequency: int = Field(ge=2)
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Literal["low", "medium", "high", "critical"]
    source_evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator(
        "failure_pattern_id",
        "pattern_key",
        "problem_statement",
    )
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "self-improvement failure pattern text")
        return cleaned

    @field_validator(
        "source_observation_ids",
        "source_learning_pattern_ids",
        "source_experience_ids",
        "source_evidence_refs",
    )
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement failure pattern reference")
        return cleaned

    @model_validator(mode="after")
    def pattern_must_be_repeated_and_side_effect_free(self) -> ImprovementFailurePattern:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("failure pattern must use the AION-169 experiment authorization")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError("failure patterns cannot modify source, Git, PRs, or runtime state")
        evidence_count = (
            len(self.source_observation_ids)
            + len(self.source_learning_pattern_ids)
            + len(self.source_experience_ids)
        )
        if evidence_count == 0:
            raise ValueError("failure pattern requires source records")
        return self


def intake_failure_pattern(
    *,
    failure_pattern_id: str,
    observations: Iterable[ImprovementObservation],
    learning_patterns: Iterable[LearningPattern] = (),
    experiences: Iterable[ExperienceRecord] = (),
    min_frequency: int = 2,
) -> ImprovementFailurePattern:
    """Create one deterministic repeated failure pattern from read-only inputs."""

    observation_list = tuple(observations)
    learning_pattern_list = tuple(learning_patterns)
    experience_list = tuple(experiences)
    if not observation_list and not learning_pattern_list and not experience_list:
        raise ValueError("failure-pattern intake requires at least one source record")

    frequency = max(
        sum(item.repeated_count for item in observation_list),
        *(pattern.frequency for pattern in learning_pattern_list),
        len(experience_list),
        min_frequency,
    )
    if frequency < min_frequency:
        raise ValueError("failure pattern did not meet minimum frequency")

    pattern_type = _pattern_type(observation_list, learning_pattern_list, experience_list)
    confidence = _confidence(observation_list, learning_pattern_list, experience_list)
    severity = _severity(pattern_type, frequency, confidence)
    source_refs = _source_refs(observation_list, learning_pattern_list, experience_list)
    pattern_key = _pattern_key(observation_list, learning_pattern_list, experience_list)
    return ImprovementFailurePattern(
        failure_pattern_id=failure_pattern_id,
        pattern_type=pattern_type,
        pattern_key=pattern_key,
        problem_statement=_problem_statement(pattern_key, pattern_type, frequency),
        source_observation_ids=tuple(item.observation_id for item in observation_list),
        source_learning_pattern_ids=tuple(item.pattern_id for item in learning_pattern_list),
        source_experience_ids=tuple(item.experience_id for item in experience_list),
        frequency=frequency,
        confidence=confidence,
        severity=severity,
        source_evidence_refs=source_refs,
        created_at=utc_now(),
    )


def _pattern_key(
    observations: tuple[ImprovementObservation, ...],
    learning_patterns: tuple[LearningPattern, ...],
    experiences: tuple[ExperienceRecord, ...],
) -> str:
    if observations and observations[0].score_name:
        return observations[0].score_name
    if learning_patterns:
        return learning_patterns[0].pattern_type
    if experiences:
        return experiences[0].experience_type
    return "generic_failure"


def _pattern_type(
    observations: tuple[ImprovementObservation, ...],
    learning_patterns: tuple[LearningPattern, ...],
    experiences: tuple[ExperienceRecord, ...],
) -> ImprovementFailurePatternType:
    keys = {_pattern_key(observations, learning_patterns, experiences)}
    keys.update(item.score_name or "" for item in observations)
    keys.update(item.pattern_type for item in learning_patterns)
    keys.update(item.experience_type for item in experiences)
    joined = " ".join(sorted(keys))
    if "retrieval" in joined or "memory_relevance" in joined:
        return "retrieval_failure"
    if "plan" in joined or "planning" in joined:
        return "planning_failure"
    if "evidence" in joined or "grounding" in joined:
        return "evidence_grounding_failure"
    if "policy" in joined or "blocked" in joined:
        return "policy_block"
    if "regression" in joined:
        return "regression_drift"
    if "replay" in joined:
        return "replay_drift"
    return "generic_failure"


def _confidence(
    observations: tuple[ImprovementObservation, ...],
    learning_patterns: tuple[LearningPattern, ...],
    experiences: tuple[ExperienceRecord, ...],
) -> float:
    values = [1.0 - (item.observed_score or 0.5) for item in observations]
    values.extend(item.confidence for item in learning_patterns)
    values.extend(item.confidence for item in experiences)
    if not values:
        return 0.5
    return max(0.0, min(1.0, sum(values) / len(values)))


def _severity(
    pattern_type: ImprovementFailurePatternType,
    frequency: int,
    confidence: float,
) -> Literal["low", "medium", "high", "critical"]:
    if pattern_type in {"regression_drift", "replay_drift"} and frequency >= 3:
        return "high"
    if confidence >= 0.8 and frequency >= 4:
        return "high"
    if confidence >= 0.55 or frequency >= 3:
        return "medium"
    return "low"


def _source_refs(
    observations: tuple[ImprovementObservation, ...],
    learning_patterns: tuple[LearningPattern, ...],
    experiences: tuple[ExperienceRecord, ...],
) -> tuple[str, ...]:
    refs: list[str] = []
    for observation in observations:
        refs.extend(observation.source_evidence_refs)
    refs.extend(f"learning-pattern:{item.pattern_id}" for item in learning_patterns)
    refs.extend(f"experience:{item.experience_id}" for item in experiences)
    return tuple(dict.fromkeys(refs))


def _problem_statement(
    pattern_key: str,
    pattern_type: ImprovementFailurePatternType,
    frequency: int,
) -> str:
    return (
        f"Repeated {pattern_type.replace('_', ' ')} detected for {pattern_key} "
        f"across {frequency} source records."
    )


__all__ = [
    "ImprovementFailurePattern",
    "ImprovementFailurePatternType",
    "intake_failure_pattern",
]
