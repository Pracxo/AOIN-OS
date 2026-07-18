"""Deterministic candidate-slot runner for AION-170 experiments."""

from __future__ import annotations

from typing import Protocol

from aion_brain.contracts.self_improvement import ImprovementRiskLevel
from aion_brain.self_improvement.benchmark_contracts import BenchmarkMetric
from aion_brain.self_improvement.experiment import (
    ImprovementExperimentPlan,
    ImprovementExperimentResult,
    approval_tier_for_risk,
)
from aion_brain.self_improvement.scoring import (
    metrics_meet_thresholds,
    require_required_metric_set,
    score_metric_set,
)


class ExperimentCandidateProvider(Protocol):
    """Protocol for explicitly configured candidate metric providers."""

    provider_id: str

    def candidate_metrics(
        self,
        plan: ImprovementExperimentPlan,
    ) -> tuple[BenchmarkMetric, ...]:
        """Return deterministic candidate metrics for a plan."""


class DisabledExperimentCandidateProvider:
    """Fail-closed runtime default; no autonomous candidate execution."""

    provider_id = "disabled-experiment-candidate-provider"

    def candidate_metrics(
        self,
        plan: ImprovementExperimentPlan,  # noqa: ARG002
    ) -> tuple[BenchmarkMetric, ...]:
        raise RuntimeError("self-improvement experiment candidate execution is disabled")


class DeterministicExperimentCandidateProvider:
    """Deterministic test double that treats target metrics as the candidate slot."""

    provider_id = "deterministic-test-experiment-candidate-provider"

    def candidate_metrics(
        self,
        plan: ImprovementExperimentPlan,
    ) -> tuple[BenchmarkMetric, ...]:
        return plan.target_metrics


class ImprovementExperimentRunner:
    """Run a bounded baseline/candidate comparison without source or Git side effects."""

    def __init__(
        self,
        candidate_provider: ExperimentCandidateProvider | None = None,
    ) -> None:
        self._candidate_provider = candidate_provider or DisabledExperimentCandidateProvider()

    def run(
        self,
        plan: ImprovementExperimentPlan,
        *,
        experiment_result_id: str | None = None,
        candidate_metrics: tuple[BenchmarkMetric, ...] | None = None,
    ) -> ImprovementExperimentResult:
        """Run the candidate slot and return a fail-closed result."""

        require_required_metric_set(plan.baseline_metrics)
        require_required_metric_set(plan.target_metrics)
        candidate = candidate_metrics or self._candidate_provider.candidate_metrics(plan)
        require_required_metric_set(candidate)

        benchmark_passed = metrics_meet_thresholds(candidate) and _targets_met(
            candidate,
            plan.target_metrics,
        )
        safety_passed = benchmark_passed and not (
            plan.source_modified
            or plan.git_branch_created
            or plan.pr_created
            or plan.runtime_effect
        )
        risk_level = _risk_level(plan=plan, safety_passed=safety_passed)
        reason_codes = _reason_codes(safety_passed=safety_passed, benchmark_passed=benchmark_passed)
        return ImprovementExperimentResult(
            experiment_result_id=experiment_result_id
            or f"experiment-result-{plan.experiment_plan_id}",
            experiment_plan_id=plan.experiment_plan_id,
            candidate_slot_id=plan.candidate_slot_id,
            baseline_metrics=plan.baseline_metrics,
            candidate_metrics=candidate,
            target_metrics=plan.target_metrics,
            safety_passed=safety_passed,
            benchmark_passed=benchmark_passed,
            experiment_success=safety_passed and benchmark_passed,
            quality_score=score_metric_set(candidate),
            risk_level=risk_level,
            approval_tier=approval_tier_for_risk(risk_level),
            reason_codes=reason_codes,
            created_at=plan.created_at,
        )


def _targets_met(
    candidate_metrics: tuple[BenchmarkMetric, ...],
    target_metrics: tuple[BenchmarkMetric, ...],
) -> bool:
    candidate_by_name = require_required_metric_set(candidate_metrics)
    target_by_name = require_required_metric_set(target_metrics)
    for name, target in target_by_name.items():
        candidate = candidate_by_name[name]
        if target.higher_is_better and candidate.value < target.value:
            return False
        if not target.higher_is_better and candidate.value > target.value:
            return False
    return True


def _risk_level(
    *,
    plan: ImprovementExperimentPlan,
    safety_passed: bool,
) -> ImprovementRiskLevel:
    if not safety_passed:
        return "high"
    if any(path.startswith("services/brain-api/src/") for path in plan.allowed_paths):
        return "medium"
    return "low"


def _reason_codes(*, safety_passed: bool, benchmark_passed: bool) -> tuple[str, ...]:
    reasons: list[str] = []
    if not benchmark_passed:
        reasons.append("benchmark_target_not_met")
    if not safety_passed:
        reasons.append("safety_gate_not_met")
    if not reasons:
        reasons.append("approval_pending_human_review_required")
    return tuple(reasons)


__all__ = [
    "DeterministicExperimentCandidateProvider",
    "DisabledExperimentCandidateProvider",
    "ExperimentCandidateProvider",
    "ImprovementExperimentRunner",
]
