"""Pure controlled pipeline for self-improvement shadow-mode runs."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.self_improvement_shadow import (
    DEFAULT_MAXIMUM_CONCURRENCY,
    FROZEN_MODEL_CONFIG,
    SHADOW_HYPOTHESIS_SCHEMA_VERSION,
    SHADOW_PATTERN_SCHEMA_VERSION,
    SHADOW_PROPOSAL_SCHEMA_VERSION,
    SHADOW_REGRESSION_PROPOSAL_SCHEMA_VERSION,
    SHADOW_REVIEW_ITEM_SCHEMA_VERSION,
    ShadowChangeType,
    ShadowMetricName,
    ShadowObservationManifest,
    ShadowPatternType,
    ShadowRiskLevel,
    fingerprint_model,
    require_fingerprint,
    require_reason_codes,
    require_safe_identifier,
    require_utc_datetime,
    utc_now,
    validate_shadow_text,
)
from aion_brain.self_improvement.shadow_budget import (
    ShadowResourceBudget,
    ShadowResourceUsage,
    evaluate_shadow_budget,
)
from aion_brain.self_improvement.shadow_evidence import (
    ShadowAuditEvent,
    ShadowBudgetFailureRecord,
    ShadowEvidenceBundle,
    ShadowProvenanceRecord,
    ShadowRunDiagnostics,
)
from aion_brain.self_improvement.shadow_mode import (
    build_shadow_evaluation_summary,
    default_shadow_expires_at,
)
from aion_brain.self_improvement.shadow_observation import (
    DisabledShadowReferenceAdapter,
    ShadowObservationRecord,
    ShadowReferenceAdapter,
    ShadowReferenceResolutionError,
    ShadowReferenceSnapshot,
    observation_from_shadow_snapshot,
)
from aion_brain.self_improvement.shadow_redaction import validate_shadow_safe_value

ShadowIdFactory = Callable[[str, int], str]

REGRESSION_TEST_AREAS: tuple[str, ...] = (
    "brain_api_retrieval_tests",
    "brain_api_planning_tests",
    "brain_api_grounding_tests",
    "brain_api_policy_tests",
    "brain_api_regression_tests",
    "self_improvement_shadow_tests",
)
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class ShadowFailurePatternCandidate(BaseModel):
    """Repeated redacted failure pattern candidate."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_PATTERN_SCHEMA_VERSION
    failure_pattern_id: str = Field(min_length=1, max_length=128)
    pattern_type: ShadowPatternType
    pattern_key: str = Field(min_length=1, max_length=128)
    problem_summary: str = Field(min_length=1, max_length=512)
    source_observation_ids: tuple[str, ...] = Field(min_length=1, max_length=1000)
    source_reference_fingerprints: tuple[str, ...] = Field(min_length=1, max_length=1000)
    frequency: int = Field(ge=2)
    confidence: float = Field(ge=0.0, le=1.0)
    severity: ShadowRiskLevel
    review_state: str = "shadow_pattern_detected"
    created_at: datetime
    fingerprint: str = ""

    @field_validator("failure_pattern_id", "pattern_key")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("problem_summary")
    @classmethod
    def problem_summary_is_safe(cls, value: str) -> str:
        return validate_shadow_text(value, max_length=512)

    @field_validator("source_observation_ids")
    @classmethod
    def source_observation_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_safe_identifier(item) for item in value)

    @field_validator("source_reference_fingerprints")
    @classmethod
    def source_reference_fingerprints_are_sha256(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_fingerprint(item) for item in value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def pattern_is_valid(self) -> ShadowFailurePatternCandidate:
        if self.review_state != "shadow_pattern_detected":
            raise ValueError("shadow pattern state mismatch")
        if self.severity == "critical":
            raise ValueError("critical shadow patterns require separate protected-core evidence")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowHypothesisCandidate(BaseModel):
    """Bounded template-generated shadow hypothesis."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_HYPOTHESIS_SCHEMA_VERSION
    hypothesis_id: str = Field(min_length=1, max_length=128)
    failure_pattern_id: str = Field(min_length=1, max_length=128)
    statement: str = Field(min_length=1, max_length=512)
    change_type: ShadowChangeType
    target_metric: ShadowMetricName
    target_direction: str
    target_delta: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_scope_labels: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    requires_separate_authorization: bool
    review_state: str = "shadow_hypothesis_generated"
    created_at: datetime
    fingerprint: str = ""

    @field_validator("hypothesis_id", "failure_pattern_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("statement")
    @classmethod
    def statement_is_safe(cls, value: str) -> str:
        return validate_shadow_text(value, max_length=512)

    @field_validator("target_direction")
    @classmethod
    def target_direction_is_valid(cls, value: str) -> str:
        if value not in {"increase", "decrease"}:
            raise ValueError("shadow target direction mismatch")
        return value

    @field_validator("suggested_scope_labels")
    @classmethod
    def scope_labels_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_shadow_text(item, max_length=128) for item in value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def hypothesis_is_valid(self) -> ShadowHypothesisCandidate:
        if self.review_state != "shadow_hypothesis_generated":
            raise ValueError("shadow hypothesis state mismatch")
        if self.change_type == "governance_review" and not self.requires_separate_authorization:
            raise ValueError("governance review requires separate authorization")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowRegressionTestProposal(BaseModel):
    """Specification-only regression-test proposal."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_REGRESSION_PROPOSAL_SCHEMA_VERSION
    regression_proposal_id: str = Field(min_length=1, max_length=128)
    hypothesis_id: str = Field(min_length=1, max_length=128)
    failure_pattern_id: str = Field(min_length=1, max_length=128)
    test_name: str = Field(min_length=1, max_length=128)
    suggested_test_area: str = Field(min_length=1, max_length=128)
    failing_condition: str = Field(min_length=1, max_length=512)
    expected_behavior: str = Field(min_length=1, max_length=512)
    proposed_assertion_summaries: tuple[str, ...] = Field(min_length=1, max_length=10)
    source_reference_fingerprints: tuple[str, ...] = Field(min_length=1, max_length=1000)
    review_state: str = "shadow_regression_proposed"
    created_at: datetime
    fingerprint: str = ""

    @field_validator("regression_proposal_id", "hypothesis_id", "failure_pattern_id", "test_name")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("suggested_test_area")
    @classmethod
    def test_area_is_allowed(cls, value: str) -> str:
        if value not in REGRESSION_TEST_AREAS:
            raise ValueError("shadow test area is not allowed")
        return value

    @field_validator("failing_condition", "expected_behavior")
    @classmethod
    def text_is_safe(cls, value: str) -> str:
        return validate_shadow_text(value, max_length=512)

    @field_validator("proposed_assertion_summaries")
    @classmethod
    def assertions_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_shadow_text(item, max_length=256) for item in value)

    @field_validator("source_reference_fingerprints")
    @classmethod
    def source_reference_fingerprints_are_sha256(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_fingerprint(item) for item in value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def proposal_is_spec_only(self) -> ShadowRegressionTestProposal:
        if self.review_state != "shadow_regression_proposed":
            raise ValueError("shadow regression proposal state mismatch")
        forbidden_text = " ".join(
            (self.failing_condition, self.expected_behavior, *self.proposed_assertion_summaries)
        ).lower()
        for marker in ("skip", "delete assertion", "broad exclusion", "threshold change"):
            if marker in forbidden_text:
                raise ValueError("shadow regression proposal weakens tests")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowImprovementProposalCandidate(BaseModel):
    """Review-only shadow improvement proposal candidate."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_PROPOSAL_SCHEMA_VERSION
    shadow_proposal_id: str = Field(min_length=1, max_length=128)
    failure_pattern_id: str = Field(min_length=1, max_length=128)
    hypothesis_id: str = Field(min_length=1, max_length=128)
    regression_proposal_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=25)
    problem_summary: str = Field(min_length=1, max_length=512)
    change_type: ShadowChangeType
    target_metric: ShadowMetricName
    target_direction: str
    target_delta: float = Field(ge=0.0, le=1.0)
    risk_level: ShadowRiskLevel
    source_reference_fingerprints: tuple[str, ...] = Field(min_length=1, max_length=1000)
    suggested_scope_labels: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    requires_separate_authorization: bool
    operator_review_required: bool = True
    review_state: str = "shadow_proposal_generated"
    created_at: datetime
    implementation_authorization_created: bool = False
    approval_created: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    merged: bool = False
    runtime_effect: bool = False
    active_learning_promoted: bool = False
    fingerprint: str = ""

    @field_validator("shadow_proposal_id", "failure_pattern_id", "hypothesis_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("regression_proposal_ids")
    @classmethod
    def regression_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_safe_identifier(item) for item in value)

    @field_validator("problem_summary")
    @classmethod
    def problem_summary_is_safe(cls, value: str) -> str:
        return validate_shadow_text(value, max_length=512)

    @field_validator("target_direction")
    @classmethod
    def target_direction_is_valid(cls, value: str) -> str:
        if value not in {"increase", "decrease"}:
            raise ValueError("shadow target direction mismatch")
        return value

    @field_validator("source_reference_fingerprints")
    @classmethod
    def source_reference_fingerprints_are_sha256(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_fingerprint(item) for item in value)

    @field_validator("suggested_scope_labels")
    @classmethod
    def scope_labels_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_shadow_text(item, max_length=128) for item in value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def proposal_is_review_only(self) -> ShadowImprovementProposalCandidate:
        if self.review_state != "shadow_proposal_generated" or not self.operator_review_required:
            raise ValueError("shadow proposal must require operator review")
        if self.risk_level in {"high", "critical"} and not self.requires_separate_authorization:
            raise ValueError("high-risk shadow proposal requires separate authorization")
        if any(
            (
                self.implementation_authorization_created,
                self.approval_created,
                self.source_modified,
                self.git_mutated,
                self.pull_request_created,
                self.merged,
                self.runtime_effect,
                self.active_learning_promoted,
            )
        ):
            raise ValueError("shadow proposal cannot create side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowOperatorReviewItem(BaseModel):
    """Operator review item derived from one shadow proposal."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_REVIEW_ITEM_SCHEMA_VERSION
    review_item_id: str = Field(min_length=1, max_length=128)
    shadow_proposal_id: str = Field(min_length=1, max_length=128)
    observation_summary: str = Field(min_length=1, max_length=512)
    pattern_summary: str = Field(min_length=1, max_length=512)
    hypothesis_summary: str = Field(min_length=1, max_length=512)
    regression_test_summary: str = Field(min_length=1, max_length=512)
    policy_delta_summary: str = Field(min_length=1, max_length=512)
    risk_level: ShadowRiskLevel
    budget_status: str = Field(min_length=1, max_length=128)
    source_reference_fingerprints: tuple[str, ...] = Field(default_factory=tuple, max_length=1000)
    reason_codes: tuple[str, ...]
    review_state: str = "operator_review_pending"
    operator_review_required: bool = True
    created_at: datetime
    expires_at: datetime
    implementation_authorization_created: bool = False
    approval_created: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    merged: bool = False
    runtime_effect: bool = False
    active_learning_promoted: bool = False
    fingerprint: str = ""

    @field_validator("review_item_id", "shadow_proposal_id", "budget_status")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator(
        "observation_summary",
        "pattern_summary",
        "hypothesis_summary",
        "regression_test_summary",
        "policy_delta_summary",
    )
    @classmethod
    def summaries_are_safe(cls, value: str) -> str:
        return validate_shadow_text(value, max_length=512)

    @field_validator("source_reference_fingerprints")
    @classmethod
    def source_reference_fingerprints_are_sha256(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_fingerprint(item) for item in value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return require_reason_codes(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def review_item_is_evidence_only(self) -> ShadowOperatorReviewItem:
        if self.review_state != "operator_review_pending" or not self.operator_review_required:
            raise ValueError("shadow review item must be pending operator review")
        if self.expires_at < self.created_at:
            raise ValueError("shadow review expiry must not precede creation")
        if any(
            (
                self.implementation_authorization_created,
                self.approval_created,
                self.source_modified,
                self.git_mutated,
                self.pull_request_created,
                self.merged,
                self.runtime_effect,
                self.active_learning_promoted,
            )
        ):
            raise ValueError("shadow review item cannot create side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


def mine_shadow_failure_patterns(
    observations: Iterable[ShadowObservationRecord],
    *,
    maximum_patterns: int,
    created_at: datetime | None = None,
) -> tuple[ShadowFailurePatternCandidate, ...]:
    """Mine repeated failure-pattern candidates from redacted observations."""

    if maximum_patterns < 0 or maximum_patterns > 100:
        raise ValueError("maximum shadow patterns out of range")
    grouped: dict[tuple[ShadowPatternType, str], list[ShadowObservationRecord]] = defaultdict(list)
    for observation in observations:
        grouped[(observation.problem_category, observation.weakest_metric)].append(observation)

    candidates: list[ShadowFailurePatternCandidate] = []
    timestamp = created_at or utc_now()
    for index, ((pattern_type, pattern_key), items) in enumerate(sorted(grouped.items()), start=1):
        unique_observations = tuple({item.observation_id: item for item in items}.values())
        unique_ids = tuple(item.observation_id for item in unique_observations)
        source_repetition: dict[tuple[str, ...], int] = {}
        for observation in unique_observations:
            source_key = tuple(observation.evidence_reference_fingerprints)
            source_repetition[source_key] = max(
                source_repetition.get(source_key, 0),
                observation.repeated_count,
            )
        frequency = max(len(source_repetition), sum(source_repetition.values()))
        if frequency < 2:
            continue
        confidence = min(1.0, max(0.0, frequency / 5.0))
        severity = _severity(pattern_type, frequency, confidence)
        fingerprints = tuple(
            dict.fromkeys(
                fingerprint
                for observation in unique_observations
                for fingerprint in observation.evidence_reference_fingerprints
            )
        )
        candidates.append(
            ShadowFailurePatternCandidate(
                failure_pattern_id=f"shadow-pattern-{index}",
                pattern_type=pattern_type,
                pattern_key=pattern_key,
                problem_summary=(
                    f"Repeated {pattern_type.replace('_', ' ')} for {pattern_key} "
                    f"across {frequency} redacted observations."
                ),
                source_observation_ids=unique_ids,
                source_reference_fingerprints=fingerprints,
                frequency=frequency,
                confidence=confidence,
                severity=severity,
                created_at=timestamp,
            )
        )
    return tuple(sorted(candidates, key=_pattern_sort_key)[:maximum_patterns])


def generate_shadow_hypotheses(
    patterns: Iterable[ShadowFailurePatternCandidate],
    *,
    maximum_hypotheses: int,
    created_at: datetime | None = None,
) -> tuple[ShadowHypothesisCandidate, ...]:
    """Generate bounded template hypotheses from shadow patterns."""

    if maximum_hypotheses < 0 or maximum_hypotheses > 50:
        raise ValueError("maximum shadow hypotheses out of range")
    timestamp = created_at or utc_now()
    candidates: list[ShadowHypothesisCandidate] = []
    for index, pattern in enumerate(tuple(patterns), start=1):
        change_type, metric, direction = _hypothesis_mapping(pattern.pattern_type)
        separate = change_type in {"governance_review", "prompt_policy_review"}
        candidates.append(
            ShadowHypothesisCandidate(
                hypothesis_id=f"shadow-hypothesis-{index}",
                failure_pattern_id=pattern.failure_pattern_id,
                statement=(
                    f"Review {pattern.pattern_key} with a bounded "
                    f"{change_type.replace('_', ' ')} to {direction} {metric}."
                ),
                change_type=change_type,
                target_metric=metric,
                target_direction=direction,
                target_delta=min(1.0, max(0.01, pattern.confidence / 10.0)),
                confidence=pattern.confidence,
                suggested_scope_labels=(pattern.pattern_type, change_type),
                requires_separate_authorization=separate,
                created_at=timestamp,
            )
        )
    return tuple(candidates[:maximum_hypotheses])


def generate_shadow_regression_proposals(
    hypotheses: Iterable[ShadowHypothesisCandidate],
    *,
    maximum_proposals: int,
    created_at: datetime | None = None,
) -> tuple[ShadowRegressionTestProposal, ...]:
    """Generate specification-only regression-test proposal records."""

    if maximum_proposals < 0 or maximum_proposals > 25:
        raise ValueError("maximum shadow regression proposals out of range")
    timestamp = created_at or utc_now()
    proposals: list[ShadowRegressionTestProposal] = []
    for index, hypothesis in enumerate(tuple(hypotheses), start=1):
        proposals.append(
            ShadowRegressionTestProposal(
                regression_proposal_id=f"shadow-regression-{index}",
                hypothesis_id=hypothesis.hypothesis_id,
                failure_pattern_id=hypothesis.failure_pattern_id,
                test_name=f"shadow_test_{hypothesis.target_metric}",
                suggested_test_area=_test_area_for(hypothesis.change_type),
                failing_condition=f"Redacted metric {hypothesis.target_metric} misses target.",
                expected_behavior=(
                    f"Future separately authorized work should {hypothesis.target_direction} "
                    f"{hypothesis.target_metric} without side effects."
                ),
                proposed_assertion_summaries=(
                    "Candidate remains review only.",
                    "Runtime influence remains false.",
                    "Separate governance review is required before implementation.",
                ),
                source_reference_fingerprints=(
                    fingerprint_model(hypothesis),
                ),
                created_at=timestamp,
            )
        )
    return tuple(proposals[:maximum_proposals])


def generate_shadow_improvement_proposals(
    hypotheses: Iterable[ShadowHypothesisCandidate],
    regression_proposals: Iterable[ShadowRegressionTestProposal],
    patterns: Iterable[ShadowFailurePatternCandidate],
    *,
    maximum_proposals: int,
    created_at: datetime | None = None,
) -> tuple[ShadowImprovementProposalCandidate, ...]:
    """Project review-only shadow proposal candidates."""

    if maximum_proposals < 0 or maximum_proposals > 10:
        raise ValueError("maximum shadow proposals out of range")
    timestamp = created_at or utc_now()
    by_hypothesis = {item.hypothesis_id: item for item in regression_proposals}
    by_pattern = {item.failure_pattern_id: item for item in patterns}
    proposals: list[ShadowImprovementProposalCandidate] = []
    for index, hypothesis in enumerate(tuple(hypotheses), start=1):
        pattern = by_pattern[hypothesis.failure_pattern_id]
        regression = by_hypothesis.get(hypothesis.hypothesis_id)
        risk = _risk_for(hypothesis.change_type)
        proposals.append(
            ShadowImprovementProposalCandidate(
                shadow_proposal_id=f"shadow-proposal-{index}",
                failure_pattern_id=hypothesis.failure_pattern_id,
                hypothesis_id=hypothesis.hypothesis_id,
                regression_proposal_ids=(
                    (regression.regression_proposal_id,) if regression is not None else ()
                ),
                problem_summary=pattern.problem_summary,
                change_type=hypothesis.change_type,
                target_metric=hypothesis.target_metric,
                target_direction=hypothesis.target_direction,
                target_delta=hypothesis.target_delta,
                risk_level=risk,
                source_reference_fingerprints=pattern.source_reference_fingerprints,
                suggested_scope_labels=hypothesis.suggested_scope_labels,
                requires_separate_authorization=(
                    hypothesis.requires_separate_authorization or risk in {"high", "critical"}
                ),
                created_at=timestamp,
            )
        )
    return tuple(proposals[:maximum_proposals])


def project_shadow_operator_review_items(
    proposals: Iterable[ShadowImprovementProposalCandidate],
    *,
    budget_status: str,
    created_at: datetime,
    expires_at: datetime,
) -> tuple[ShadowOperatorReviewItem, ...]:
    """Create operator review items from shadow proposal candidates."""

    review_items: list[ShadowOperatorReviewItem] = []
    for index, proposal in enumerate(tuple(proposals), start=1):
        review_items.append(
            ShadowOperatorReviewItem(
                review_item_id=f"shadow-review-{index}",
                shadow_proposal_id=proposal.shadow_proposal_id,
                observation_summary=proposal.problem_summary,
                pattern_summary=f"Pattern {proposal.failure_pattern_id} requires review.",
                hypothesis_summary=f"Hypothesis {proposal.hypothesis_id} remains advisory.",
                regression_test_summary="Regression proposal is specification only.",
                policy_delta_summary="No policy change is applied.",
                risk_level=proposal.risk_level,
                budget_status=budget_status,
                source_reference_fingerprints=proposal.source_reference_fingerprints,
                reason_codes=("shadow_operator_review_required",),
                created_at=created_at,
                expires_at=expires_at,
            )
        )
    return tuple(review_items)


class ControlledShadowPipeline:
    """Operator-invoked, read-only, deterministic shadow pipeline."""

    def __init__(
        self,
        *,
        reference_adapter: ShadowReferenceAdapter | None = None,
        resource_budget: ShadowResourceBudget | None = None,
        clock: Callable[[], datetime] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
        id_factory: ShadowIdFactory | None = None,
    ) -> None:
        self._reference_adapter = reference_adapter or DisabledShadowReferenceAdapter()
        self._resource_budget = resource_budget or ShadowResourceBudget()
        self._clock = clock or utc_now
        self._monotonic_clock = monotonic_clock or time.monotonic
        self._id_factory = id_factory or _default_id_factory

    def run(self, manifest: ShadowObservationManifest) -> ShadowEvidenceBundle:
        """Run one explicit shadow-mode pipeline and return immutable evidence."""

        created_at = self._clock()
        started = self._monotonic_clock()
        run_id = self._id_factory("shadow-run", 1)
        manifest_fingerprint = fingerprint_model(manifest, fingerprint_field="unused")
        pre_usage = ShadowResourceUsage(
            observation_references=len(manifest.references),
            concurrency=manifest.maximum_concurrency,
            benchmark_cost_units=manifest.benchmark_cost_units,
        )
        pre_decision = evaluate_shadow_budget(pre_usage, self._resource_budget)
        if not pre_decision.within_budget:
            return self._budget_blocked_bundle(
                run_id=run_id,
                manifest=manifest,
                manifest_fingerprint=manifest_fingerprint,
                usage=pre_usage,
                created_at=created_at,
                wall_clock_seconds=self._elapsed(started),
            )

        try:
            snapshots = self._resolve_references(manifest)
        except ShadowReferenceResolutionError:
            return self._reference_unavailable_bundle(
                run_id=run_id,
                manifest=manifest,
                manifest_fingerprint=manifest_fingerprint,
                created_at=created_at,
                wall_clock_seconds=self._elapsed(started),
            )

        for snapshot in snapshots:
            validate_shadow_safe_value(snapshot.model_dump(mode="python"))

        observations = tuple(
            observation_from_shadow_snapshot(
                snapshot,
                observation_id=self._id_factory("shadow-observation", index),
                created_at=created_at,
            )
            for index, snapshot in enumerate(snapshots, start=1)
        )
        evaluation = build_shadow_evaluation_summary(
            evaluation_id=self._id_factory("shadow-evaluation", 1),
            observations=observations,
            benchmark_cost_units=manifest.benchmark_cost_units,
            created_at=created_at,
        )
        patterns = mine_shadow_failure_patterns(
            observations,
            maximum_patterns=self._resource_budget.maximum_failure_patterns,
            created_at=created_at,
        )
        hypotheses = generate_shadow_hypotheses(
            patterns,
            maximum_hypotheses=self._resource_budget.maximum_hypotheses,
            created_at=created_at,
        )
        regressions = generate_shadow_regression_proposals(
            hypotheses,
            maximum_proposals=self._resource_budget.maximum_regression_test_proposals,
            created_at=created_at,
        )
        proposals = generate_shadow_improvement_proposals(
            hypotheses,
            regressions,
            patterns,
            maximum_proposals=self._resource_budget.maximum_shadow_proposals,
            created_at=created_at,
        )
        expires_at = default_shadow_expires_at(created_at, manifest.retention_seconds)
        review_items = project_shadow_operator_review_items(
            proposals,
            budget_status="within_budget",
            created_at=created_at,
            expires_at=expires_at,
        )
        usage = ShadowResourceUsage(
            observation_references=len(manifest.references),
            evaluation_records=1,
            failure_patterns=len(patterns),
            hypotheses=len(hypotheses),
            regression_test_proposals=len(regressions),
            shadow_proposals=len(proposals),
            concurrency=manifest.maximum_concurrency,
            wall_clock_seconds=self._elapsed(started),
            benchmark_cost_units=manifest.benchmark_cost_units,
        )
        decision = evaluate_shadow_budget(usage, self._resource_budget)
        if not decision.within_budget:
            return self._budget_blocked_bundle(
                run_id=run_id,
                manifest=manifest,
                manifest_fingerprint=manifest_fingerprint,
                usage=usage,
                created_at=created_at,
                wall_clock_seconds=usage.wall_clock_seconds,
            )
        outcome = "completed" if patterns else "completed_without_pattern"
        reason_codes = (
            ("shadow_run_completed", "shadow_pattern_detected")
            if patterns
            else ("shadow_run_completed_without_pattern", "shadow_no_repeated_pattern")
        )
        return self._bundle(
            run_id=run_id,
            manifest=manifest,
            manifest_fingerprint=manifest_fingerprint,
            outcome=outcome,
            observations=observations,
            evaluation=evaluation,
            patterns=patterns,
            hypotheses=hypotheses,
            regressions=regressions,
            proposals=proposals,
            review_items=review_items,
            usage=usage,
            reason_codes=reason_codes,
            created_at=created_at,
            expires_at=expires_at,
        )

    def _resolve_references(
        self,
        manifest: ShadowObservationManifest,
    ) -> tuple[ShadowReferenceSnapshot, ...]:
        workers = min(
            manifest.maximum_concurrency,
            self._resource_budget.maximum_concurrency,
            DEFAULT_MAXIMUM_CONCURRENCY,
        )
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self._reference_adapter.resolve, reference)
                for reference in manifest.references
            ]
            return tuple(future.result() for future in futures)

    def _bundle(
        self,
        *,
        run_id: str,
        manifest: ShadowObservationManifest,
        manifest_fingerprint: str,
        outcome: str,
        observations: tuple[ShadowObservationRecord, ...],
        evaluation: Any | None,
        patterns: tuple[ShadowFailurePatternCandidate, ...],
        hypotheses: tuple[ShadowHypothesisCandidate, ...],
        regressions: tuple[ShadowRegressionTestProposal, ...],
        proposals: tuple[ShadowImprovementProposalCandidate, ...],
        review_items: tuple[ShadowOperatorReviewItem, ...],
        usage: ShadowResourceUsage,
        reason_codes: tuple[str, ...],
        created_at: datetime,
        expires_at: datetime,
        budget_decision: Any | None = None,
        budget_failure: ShadowBudgetFailureRecord | None = None,
    ) -> ShadowEvidenceBundle:
        decision = budget_decision or evaluate_shadow_budget(usage, self._resource_budget)
        diagnostics = ShadowRunDiagnostics(
            run_id=run_id,
            reference_count=len(manifest.references),
            observation_count=len(observations),
            evaluation_count=1 if evaluation is not None else 0,
            pattern_count=len(patterns),
            hypothesis_count=len(hypotheses),
            regression_proposal_count=len(regressions),
            shadow_proposal_count=len(proposals),
            operator_review_item_count=len(review_items),
            wall_clock_seconds=usage.wall_clock_seconds,
            benchmark_cost_units=usage.benchmark_cost_units,
            output_bytes=usage.output_bytes,
            output_files=usage.output_files,
            created_at=created_at,
        )
        audit = ShadowAuditEvent(
            audit_event_id=f"audit-{run_id}",
            run_id=run_id,
            event_type=reason_codes[0],
            reason_codes=reason_codes,
            reference_count=len(manifest.references),
            created_at=created_at,
        )
        provenance = ShadowProvenanceRecord(
            provenance_record_id=f"provenance-{run_id}",
            run_id=run_id,
            manifest_fingerprint=manifest_fingerprint,
            reference_fingerprints=tuple(
                item.reference_fingerprint for item in manifest.references
            ),
            observation_ids=tuple(item.observation_id for item in observations),
            pattern_ids=tuple(item.failure_pattern_id for item in patterns),
            hypothesis_ids=tuple(item.hypothesis_id for item in hypotheses),
            proposal_ids=tuple(item.shadow_proposal_id for item in proposals),
            review_item_ids=tuple(item.review_item_id for item in review_items),
            created_at=created_at,
        )
        return ShadowEvidenceBundle(
            run_id=run_id,
            manifest_id=manifest.manifest_id,
            manifest_fingerprint=manifest_fingerprint,
            outcome=outcome,  # type: ignore[arg-type]
            observations=observations,
            evaluation_summary=evaluation,
            failure_patterns=patterns,
            hypotheses=hypotheses,
            regression_test_proposals=regressions,
            shadow_proposals=proposals,
            operator_review_items=review_items,
            audit_events=(audit,),
            provenance=provenance,
            diagnostics=diagnostics,
            resource_budget=self._resource_budget,
            resource_usage=usage,
            budget_decision=decision,
            budget_failure=budget_failure,
            reason_codes=reason_codes,
            created_at=created_at,
            expires_at=expires_at,
        )

    def _budget_blocked_bundle(
        self,
        *,
        run_id: str,
        manifest: ShadowObservationManifest,
        manifest_fingerprint: str,
        usage: ShadowResourceUsage,
        created_at: datetime,
        wall_clock_seconds: float,
    ) -> ShadowEvidenceBundle:
        decision = evaluate_shadow_budget(usage, self._resource_budget)
        failure = ShadowBudgetFailureRecord(
            budget_failure_id=f"budget-failure-{run_id}",
            run_id=run_id,
            violations=decision.violations,
            reason_codes=decision.reason_codes,
            created_at=created_at,
        )
        adjusted_usage = usage.model_copy(
            update={
                "wall_clock_seconds": wall_clock_seconds,
                "benchmark_cost_units": usage.benchmark_cost_units,
            }
        )
        expires_at = default_shadow_expires_at(created_at, manifest.retention_seconds)
        bundle = self._bundle(
            run_id=run_id,
            manifest=manifest,
            manifest_fingerprint=manifest_fingerprint,
            outcome="budget_blocked",
            observations=(),
            evaluation=None,
            patterns=(),
            hypotheses=(),
            regressions=(),
            proposals=(),
            review_items=(),
            usage=adjusted_usage,
            reason_codes=("shadow_budget_exceeded", "shadow_run_stopped_fail_closed"),
            created_at=created_at,
            expires_at=expires_at,
            budget_decision=decision,
            budget_failure=failure,
        )
        return bundle

    def _reference_unavailable_bundle(
        self,
        *,
        run_id: str,
        manifest: ShadowObservationManifest,
        manifest_fingerprint: str,
        created_at: datetime,
        wall_clock_seconds: float,
    ) -> ShadowEvidenceBundle:
        usage = ShadowResourceUsage(
            observation_references=len(manifest.references),
            concurrency=manifest.maximum_concurrency,
            wall_clock_seconds=wall_clock_seconds,
            benchmark_cost_units=manifest.benchmark_cost_units,
        )
        return self._bundle(
            run_id=run_id,
            manifest=manifest,
            manifest_fingerprint=manifest_fingerprint,
            outcome="reference_unavailable",
            observations=(),
            evaluation=None,
            patterns=(),
            hypotheses=(),
            regressions=(),
            proposals=(),
            review_items=(),
            usage=usage,
            reason_codes=("shadow_reference_unavailable", "shadow_run_stopped_fail_closed"),
            created_at=created_at,
            expires_at=default_shadow_expires_at(created_at, manifest.retention_seconds),
        )

    def _elapsed(self, started: float) -> float:
        return max(0.0, self._monotonic_clock() - started)


def _default_id_factory(prefix: str, index: int) -> str:
    suffix = "".join(chr(ord("a") + int(char, 16)) for char in uuid.uuid4().hex[:16])
    return f"{prefix}-{index}-{suffix}"


def _severity(pattern_type: str, frequency: int, confidence: float) -> ShadowRiskLevel:
    if pattern_type in {"regression_drift", "replay_drift"} and frequency >= 3:
        return "high"
    if confidence >= 0.8 and frequency >= 4:
        return "high"
    if confidence >= 0.55 or frequency >= 3:
        return "medium"
    return "low"


def _pattern_sort_key(pattern: ShadowFailurePatternCandidate) -> tuple[int, float, int, str]:
    return (
        _SEVERITY_ORDER[pattern.severity],
        -pattern.confidence,
        -pattern.frequency,
        pattern.pattern_key,
    )


def _hypothesis_mapping(pattern_type: str) -> tuple[ShadowChangeType, ShadowMetricName, str]:
    if pattern_type == "retrieval_failure":
        return "retrieval_ranking_candidate", "retrieval_precision", "increase"
    if pattern_type == "planning_failure":
        return "planning_policy_candidate", "plan_success", "increase"
    if pattern_type == "evidence_grounding_failure":
        return "prompt_policy_review", "evidence_grounding", "increase"
    if pattern_type in {"regression_drift", "replay_drift"}:
        return "regression_test_candidate", "regression_count", "decrease"
    if pattern_type == "policy_block":
        return "governance_review", "policy_violation_count", "decrease"
    return "generic_review", "task_success", "increase"


def _test_area_for(change_type: str) -> str:
    if change_type == "retrieval_ranking_candidate":
        return "brain_api_retrieval_tests"
    if change_type == "planning_policy_candidate":
        return "brain_api_planning_tests"
    if change_type == "prompt_policy_review":
        return "brain_api_grounding_tests"
    if change_type == "governance_review":
        return "brain_api_policy_tests"
    if change_type == "regression_test_candidate":
        return "brain_api_regression_tests"
    return "self_improvement_shadow_tests"


def _risk_for(change_type: str) -> ShadowRiskLevel:
    if change_type == "governance_review":
        return "critical"
    if change_type == "prompt_policy_review":
        return "high"
    return "medium"


__all__ = [
    "ControlledShadowPipeline",
    "REGRESSION_TEST_AREAS",
    "ShadowFailurePatternCandidate",
    "ShadowHypothesisCandidate",
    "ShadowImprovementProposalCandidate",
    "ShadowOperatorReviewItem",
    "ShadowRegressionTestProposal",
    "generate_shadow_hypotheses",
    "generate_shadow_improvement_proposals",
    "generate_shadow_regression_proposals",
    "mine_shadow_failure_patterns",
    "project_shadow_operator_review_items",
]
