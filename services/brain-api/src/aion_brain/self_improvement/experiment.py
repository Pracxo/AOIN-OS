"""Experiment and proposal contracts for AION-170 self-improvement."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import (
    ImprovementProposalRef,
    ImprovementRiskLevel,
    freeze_evidence_payload,
    utc_now,
)
from aion_brain.self_improvement.benchmark_contracts import BenchmarkMetric
from aion_brain.self_improvement.hypothesis import ImprovementChangeType, ImprovementHypothesis
from aion_brain.self_improvement.observation import EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
from aion_brain.self_improvement.pattern_intake import ImprovementFailurePattern
from aion_brain.self_improvement.regression_proposal import RegressionTestProposal
from aion_brain.self_improvement.scoring import require_required_metric_set

ApprovalTier = Literal["operator", "owner", "dual_approval", "governance_board"]
ProposalLifecycleState = Literal["approval_pending", "blocked"]


class ImprovementExperimentPlan(BaseModel):
    """Bounded experiment plan that contains no patch or Git operation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    experiment_plan_id: str = Field(min_length=1)
    failure_pattern_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    regression_test_proposal_id: str = Field(min_length=1)
    baseline_metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    target_metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    candidate_slot_id: str = Field(min_length=1)
    allowed_paths: tuple[str, ...] = Field(min_length=1)
    prohibited_paths: tuple[str, ...] = Field(min_length=1)
    experiment_spec: dict[str, Any] = Field(default_factory=dict, validate_default=True)
    source_evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator(
        "experiment_plan_id",
        "failure_pattern_id",
        "hypothesis_id",
        "regression_test_proposal_id",
        "candidate_slot_id",
    )
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "self-improvement experiment plan text")
        return cleaned

    @field_validator("allowed_paths", "prohibited_paths", "source_evidence_refs")
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip().replace("\\", "/") for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement experiment plan reference")
        return cleaned

    @field_validator("experiment_spec", mode="before")
    @classmethod
    def experiment_spec_must_be_frozen(cls, value: Any) -> dict[str, Any]:
        if value is None:
            value = {}
        frozen = freeze_evidence_payload(value)
        if not isinstance(frozen, dict):
            raise ValueError("experiment_spec must be a mapping")
        return frozen

    @model_validator(mode="after")
    def plan_must_be_bounded_and_side_effect_free(self) -> ImprovementExperimentPlan:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("experiment plan must use the AION-169 experiment authorization")
        require_required_metric_set(self.baseline_metrics)
        require_required_metric_set(self.target_metrics)
        if set(_metric_names(self.baseline_metrics)) != set(_metric_names(self.target_metrics)):
            raise ValueError("baseline and target metric names must match")
        if set(self.allowed_paths) & set(self.prohibited_paths):
            raise ValueError("allowed paths cannot overlap prohibited paths")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError("experiment plans cannot modify source, Git, PRs, or runtime state")
        object.__setattr__(self, "experiment_spec", freeze_evidence_payload(self.experiment_spec))
        return self


class ImprovementExperimentResult(BaseModel):
    """Deterministic baseline/candidate experiment result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    experiment_result_id: str = Field(min_length=1)
    experiment_plan_id: str = Field(min_length=1)
    candidate_slot_id: str = Field(min_length=1)
    baseline_metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    candidate_metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    target_metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    safety_passed: bool
    benchmark_passed: bool
    experiment_success: bool
    quality_score: float = Field(ge=0.0, le=1.0)
    risk_level: ImprovementRiskLevel
    approval_tier: ApprovalTier
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator("experiment_result_id", "experiment_plan_id", "candidate_slot_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "self-improvement experiment result text")
        return cleaned

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "self-improvement experiment reason code")
        return value

    @model_validator(mode="after")
    def result_must_be_consistent_and_side_effect_free(self) -> ImprovementExperimentResult:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("experiment result must use the AION-169 experiment authorization")
        require_required_metric_set(self.baseline_metrics)
        require_required_metric_set(self.candidate_metrics)
        require_required_metric_set(self.target_metrics)
        expected_success = self.safety_passed and self.benchmark_passed
        if self.experiment_success != expected_success:
            raise ValueError("experiment_success must reflect safety and benchmark gates")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError("experiment results cannot modify source, Git, PRs, or runtime state")
        return self


class ImprovementProposal(BaseModel):
    """Approval-pending proposal assembled after a successful experiment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    proposal_id: str = Field(min_length=1)
    author_actor_id: str = Field(min_length=1)
    problem_statement: str = Field(min_length=1)
    source_evidence_refs: tuple[str, ...] = Field(min_length=1)
    failure_pattern_id: str = Field(min_length=1)
    baseline_metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    target_metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    change_type: ImprovementChangeType
    allowed_paths: tuple[str, ...] = Field(min_length=1)
    prohibited_paths: tuple[str, ...] = Field(min_length=1)
    test_specification: RegressionTestProposal
    experiment_specification: ImprovementExperimentPlan
    risk_level: ImprovementRiskLevel
    approval_tier: ApprovalTier
    rollback_requirement: bool
    lifecycle_state: ProposalLifecycleState = "approval_pending"
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator("proposal_id", "author_actor_id", "problem_statement", "failure_pattern_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "self-improvement proposal text")
        return cleaned

    @field_validator("source_evidence_refs", "allowed_paths", "prohibited_paths")
    @classmethod
    def tuple_values_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip().replace("\\", "/") for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement proposal reference")
        return cleaned

    @model_validator(mode="after")
    def proposal_must_bind_required_fields_and_fail_closed(self) -> ImprovementProposal:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("proposal must use the AION-169 experiment authorization")
        require_required_metric_set(self.baseline_metrics)
        require_required_metric_set(self.target_metrics)
        if self.failure_pattern_id != self.experiment_specification.failure_pattern_id:
            raise ValueError("proposal failure pattern must match experiment plan")
        if (
            self.test_specification.regression_test_proposal_id
            != self.experiment_specification.regression_test_proposal_id
        ):
            raise ValueError("proposal test specification must match experiment plan")
        if set(self.allowed_paths) & set(self.prohibited_paths):
            raise ValueError("proposal allowed paths cannot overlap prohibited paths")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError("proposals cannot modify source, Git, PRs, or runtime state")
        return self

    def to_proposal_ref(self, *, title: str | None = None) -> ImprovementProposalRef:
        """Return the governance-plane proposal reference for later approval binding."""

        return ImprovementProposalRef(
            proposal_id=self.proposal_id,
            author_actor_id=self.author_actor_id,
            title=title or self.problem_statement[:80],
            summary=self.problem_statement,
            owner_scope=("self-improvement", "AION-170"),
            risk_level=self.risk_level,
            touches_protected_core=False,
            protected_paths=(),
            evidence_refs=self.source_evidence_refs,
            created_at=utc_now(),
        )


class ImprovementEvidenceBundle(BaseModel):
    """Evidence bundle that links observations through an approval-pending proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = EXPERIMENT_AUTHORIZATION_TRANSACTION_ID
    evidence_bundle_id: str = Field(min_length=1)
    observation_ids: tuple[str, ...] = Field(min_length=1)
    failure_pattern: ImprovementFailurePattern
    hypothesis: ImprovementHypothesis
    regression_test_proposal: RegressionTestProposal
    experiment_plan: ImprovementExperimentPlan
    experiment_result: ImprovementExperimentResult
    proposal: ImprovementProposal
    evaluator_refs: tuple[str, ...] = Field(default_factory=tuple)
    learning_signal_refs: tuple[str, ...] = Field(default_factory=tuple)
    learning_pattern_refs: tuple[str, ...] = Field(default_factory=tuple)
    experience_refs: tuple[str, ...] = Field(default_factory=tuple)
    lesson_refs: tuple[str, ...] = Field(default_factory=tuple)
    skill_candidate_refs: tuple[str, ...] = Field(default_factory=tuple)
    regression_suggestion_refs: tuple[str, ...] = Field(default_factory=tuple)
    source_modified: bool = False
    git_branch_created: bool = False
    pr_created: bool = False
    runtime_effect: bool = False
    created_at: datetime

    @field_validator(
        "evidence_bundle_id",
        "observation_ids",
        "evaluator_refs",
        "learning_signal_refs",
        "learning_pattern_refs",
        "experience_refs",
        "lesson_refs",
        "skill_candidate_refs",
        "regression_suggestion_refs",
    )
    @classmethod
    def evidence_refs_must_be_safe(cls, value: str | tuple[str, ...]) -> str | tuple[str, ...]:
        if isinstance(value, str):
            reject_hidden_or_secret_text(value, "self-improvement evidence bundle text")
            return value.strip()
        cleaned = tuple(item.strip() for item in value if item.strip())
        for item in cleaned:
            reject_hidden_or_secret_text(item, "self-improvement evidence bundle reference")
        return cleaned

    @model_validator(mode="after")
    def bundle_must_bind_flow_and_remain_side_effect_free(self) -> ImprovementEvidenceBundle:
        if self.authorization_transaction_id != EXPERIMENT_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("evidence bundle must use the AION-169 experiment authorization")
        if self.failure_pattern.failure_pattern_id != self.hypothesis.failure_pattern_id:
            raise ValueError("hypothesis must reference the failure pattern")
        if self.hypothesis.hypothesis_id != self.regression_test_proposal.hypothesis_id:
            raise ValueError("test proposal must reference the hypothesis")
        if self.experiment_plan.hypothesis_id != self.hypothesis.hypothesis_id:
            raise ValueError("experiment plan must reference the hypothesis")
        if self.experiment_result.experiment_plan_id != self.experiment_plan.experiment_plan_id:
            raise ValueError("experiment result must reference the plan")
        if self.proposal.failure_pattern_id != self.failure_pattern.failure_pattern_id:
            raise ValueError("proposal must reference the failure pattern")
        if any(
            (self.source_modified, self.git_branch_created, self.pr_created, self.runtime_effect)
        ):
            raise ValueError("evidence bundles cannot modify source, Git, PRs, or runtime state")
        return self


def approval_tier_for_risk(risk_level: ImprovementRiskLevel) -> ApprovalTier:
    """Return the deterministic approval tier for a proposal risk level."""

    if risk_level == "low":
        return "operator"
    if risk_level == "medium":
        return "owner"
    if risk_level == "high":
        return "dual_approval"
    return "governance_board"


def _metric_names(metrics: tuple[BenchmarkMetric, ...]) -> tuple[str, ...]:
    return tuple(metric.metric_name for metric in metrics)


__all__ = [
    "ApprovalTier",
    "ImprovementEvidenceBundle",
    "ImprovementExperimentPlan",
    "ImprovementExperimentResult",
    "ImprovementProposal",
    "ProposalLifecycleState",
    "approval_tier_for_risk",
]
