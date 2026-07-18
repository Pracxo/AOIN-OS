from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aion_brain.contracts.experience import ExperienceRecord
from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    LearningSynthesisRun,
    LessonRecord,
    RegressionCandidateSuggestion,
    SkillCandidateSuggestion,
)
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.learning.engine import LearningEngine
from aion_brain.self_improvement import (
    DeterministicExperimentCandidateProvider,
    DeterministicTestHypothesisGenerator,
    DeterministicTestRegressionProposalGenerator,
    ImprovementExperimentRunner,
    ImprovementObservation,
    ImprovementProposalService,
)
from aion_brain.self_improvement.benchmark_contracts import (
    HIGHER_IS_BETTER_METRICS,
    REQUIRED_BENCHMARK_METRICS,
    BenchmarkMetric,
)
from aion_brain.self_improvement.experiment import ImprovementExperimentPlan

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_proposal_engine_builds_approval_pending_bundle_without_side_effects() -> None:
    traces = (_trace("trace-a"), _trace("trace-b"))
    evaluations = tuple(Evaluator().evaluate(trace) for trace in traces)
    learning_signals = tuple(
        LearningEngine().create_signal(trace=trace, evaluation=evaluation)
        for trace, evaluation in zip(traces, evaluations, strict=True)
    )
    synthesis_run = _synthesis_run()
    service = ImprovementProposalService(
        hypothesis_generator=DeterministicTestHypothesisGenerator(),
        regression_test_generator=DeterministicTestRegressionProposalGenerator(),
        experiment_runner=ImprovementExperimentRunner(DeterministicExperimentCandidateProvider()),
    )

    bundle = service.build_approval_pending_bundle(
        proposal_id="proposal-retrieval-001",
        author_actor_id="operator-aion",
        evaluation_records=evaluations,
        baseline_metrics=_baseline_metrics(),
        target_metrics=_target_metrics(),
        learning_signals=learning_signals,
        learning_synthesis_runs=(synthesis_run,),
    )

    assert bundle.proposal.lifecycle_state == "approval_pending"
    assert bundle.proposal.failure_pattern_id == bundle.failure_pattern.failure_pattern_id
    assert bundle.proposal.test_specification == bundle.regression_test_proposal
    assert bundle.experiment_result.experiment_success is True
    assert bundle.experiment_result.approval_tier in {"operator", "owner"}
    assert bundle.proposal.source_modified is False
    assert bundle.proposal.git_branch_created is False
    assert bundle.proposal.pr_created is False
    assert bundle.proposal.runtime_effect is False
    assert bundle.experiment_plan.source_modified is False
    assert bundle.experiment_result.git_branch_created is False
    assert bundle.regression_test_proposal.pr_created is False
    assert bundle.hypothesis.runtime_effect is False
    assert bundle.failure_pattern.frequency >= 2
    assert bundle.failure_pattern.pattern_type == "retrieval_failure"
    assert bundle.learning_signal_refs == (
        "learning-signal:learning-trace-a:retrieval_improvement_candidate",
        "learning-signal:learning-trace-b:retrieval_improvement_candidate",
    )
    assert bundle.learning_pattern_refs == ("learning-pattern:learning-pattern-retrieval",)
    assert bundle.experience_refs == ("experience:experience-retrieval-a",)
    assert bundle.lesson_refs == ("lesson:lesson-retrieval-a",)
    assert bundle.skill_candidate_refs == ("skill-suggestion:skill-suggestion-retrieval-a",)
    assert bundle.regression_suggestion_refs == (
        "regression-suggestion:regression-suggestion-retrieval-a",
    )

    proposal_ref = bundle.proposal.to_proposal_ref()
    assert proposal_ref.proposal_id == "proposal-retrieval-001"
    assert proposal_ref.touches_protected_core is False


def test_default_generators_are_disabled_until_explicitly_configured() -> None:
    service = ImprovementProposalService()

    with pytest.raises(RuntimeError, match="hypothesis generation is disabled"):
        service.build_approval_pending_bundle(
            proposal_id="proposal-disabled-001",
            author_actor_id="operator-aion",
            evaluation_records=tuple(Evaluator().evaluate(_trace(name)) for name in ("a", "b")),
            baseline_metrics=_baseline_metrics(),
            target_metrics=_target_metrics(),
        )


def test_failed_candidate_metrics_block_experiment_success() -> None:
    plan = _experiment_plan()
    result = ImprovementExperimentRunner().run(
        plan,
        experiment_result_id="experiment-result-failed",
        candidate_metrics=_baseline_metrics(),
    )

    assert result.benchmark_passed is False
    assert result.safety_passed is False
    assert result.experiment_success is False
    assert result.risk_level == "high"
    assert "benchmark_target_not_met" in result.reason_codes


def test_models_reject_source_git_pr_and_runtime_effects() -> None:
    with pytest.raises(ValueError, match="cannot modify source"):
        ImprovementObservation(
            observation_id="observation-side-effect",
            source_type="evaluation",
            source_ref="evaluation-side-effect",
            problem_statement="Evaluation requires bounded improvement.",
            observed_score=0.5,
            target_score=0.8,
            source_evidence_refs=("evaluation:evaluation-side-effect",),
            source_modified=True,
            created_at=_now(),
        )

    with pytest.raises(ValueError, match="cannot modify source"):
        _experiment_plan(pr_created=True)


def test_experiment_engine_scripts_are_executable_and_pass() -> None:
    for script in (
        "scripts/self-improvement-experiment-engine-no-go-regression.sh",
        "scripts/self-improvement-experiment-engine-check.sh",
    ):
        path = REPO_ROOT / script
        assert path.exists()
        assert path.stat().st_mode & 0o111
        subprocess.run([str(path)], cwd=REPO_ROOT, check=True)


def _trace(trace_id: str) -> DecisionTrace:
    return DecisionTrace(
        trace_id=trace_id,
        event_id=f"event-{trace_id}",
        intent_id=f"intent-{trace_id}",
        context_id=f"context-{trace_id}",
        plan_id=f"plan-{trace_id}",
        memory_refs=[],
        capability_refs=["capability:retrieval"],
        reasoning_refs=["reasoning:deterministic"],
        policy_decisions=["policy:allowed"],
        outcome={
            "status": "planned",
            "execution_ready": True,
            "can_create_task": True,
            "reasoning_confidence": 0.9,
            "grounding_claims": [{"verification_status": "supported"}],
        },
        created_at=_now(),
    )


def _synthesis_run() -> LearningSynthesisRun:
    experience = ExperienceRecord(
        experience_id="experience-retrieval-a",
        source_type="outcome",
        source_id="outcome-retrieval-a",
        experience_type="failure",
        status="active",
        title="Retrieval Miss",
        summary="Repeated retrieval misses required operator correction.",
        owner_scope=["self-improvement"],
        outcome_refs=["outcome-retrieval-a"],
        score=0.35,
        confidence=0.9,
        observed_at=_now(),
    )
    pattern = LearningPattern(
        pattern_id="learning-pattern-retrieval",
        pattern_type="missing_context",
        status="active",
        title="Missing Retrieval Context",
        description="Repeated missing context produced retrieval failures.",
        owner_scope=["self-improvement"],
        experience_refs=[experience.experience_id],
        outcome_refs=["outcome-retrieval-a"],
        frequency=2,
        confidence=0.9,
        severity="medium",
        recommendation="Create a bounded retrieval regression proposal.",
    )
    lesson = LessonRecord(
        lesson_id="lesson-retrieval-a",
        lesson_type="retrieval",
        status="active",
        title="Improve retrieval checks",
        lesson="Add a bounded regression check for missing retrieval context.",
        owner_scope=["self-improvement"],
        pattern_refs=[pattern.pattern_id],
        experience_refs=[experience.experience_id],
        outcome_refs=["outcome-retrieval-a"],
        confidence=0.9,
    )
    skill_suggestion = SkillCandidateSuggestion(
        suggestion_id="skill-suggestion-retrieval-a",
        pattern_id=pattern.pattern_id,
        lesson_id=lesson.lesson_id,
        title="Retrieval review checklist",
        description="Create a passive checklist suggestion for retrieval reviews.",
        owner_scope=["self-improvement"],
        proposed_skill_type="retrieval",
        source_refs=[pattern.pattern_id, lesson.lesson_id],
        risk_level="medium",
        confidence=0.8,
    )
    regression_suggestion = RegressionCandidateSuggestion(
        regression_suggestion_id="regression-suggestion-retrieval-a",
        pattern_id=pattern.pattern_id,
        outcome_id="outcome-retrieval-a",
        title="Retrieval regression candidate",
        description="A reviewable regression candidate for retrieval misses.",
        owner_scope=["self-improvement"],
        source_refs=[pattern.pattern_id],
        severity="medium",
        confidence=0.85,
    )
    return LearningSynthesisRun(
        synthesis_run_id="learning-synthesis-retrieval-a",
        status="dry_run",
        mode="dry_run",
        owner_scope=["self-improvement"],
        input_refs=["outcome:outcome-retrieval-a"],
        experiences=[experience],
        patterns=[pattern],
        lessons=[lesson],
        skill_candidate_suggestions=[skill_suggestion],
        regression_candidate_suggestions=[regression_suggestion],
        result={"code_modified": False, "skill_promoted": False},
        warnings=[],
        created_at=_now(),
        completed_at=_now(),
    )


def _experiment_plan(*, pr_created: bool = False) -> ImprovementExperimentPlan:
    return ImprovementExperimentPlan(
        experiment_plan_id="experiment-plan-unit",
        failure_pattern_id="failure-pattern-unit",
        hypothesis_id="hypothesis-unit",
        regression_test_proposal_id="regression-test-unit",
        baseline_metrics=_baseline_metrics(),
        target_metrics=_target_metrics(),
        candidate_slot_id="candidate-slot-unit",
        allowed_paths=("services/brain-api/tests/fixtures/self_improvement/",),
        prohibited_paths=(".github/", "docs/self-improvement/holdout/"),
        experiment_spec={"source_mutation_enabled": False},
        source_evidence_refs=("evaluation:evaluation-unit",),
        pr_created=pr_created,
        created_at=_now(),
    )


def _baseline_metrics() -> tuple[BenchmarkMetric, ...]:
    values = {
        "task_success": 0.6,
        "evidence_grounding": 0.6,
        "user_correction_rate": 0.1,
        "retrieval_precision": 0.55,
        "plan_success": 0.65,
        "policy_violation_count": 1.0,
        "regression_count": 1.0,
        "latency": 12.0,
        "compute_cost": 1.2,
        "rollback_count": 1.0,
        "improvement_survival": 0.8,
    }
    return _metrics(values)


def _target_metrics() -> tuple[BenchmarkMetric, ...]:
    values = {
        "task_success": 0.85,
        "evidence_grounding": 0.85,
        "user_correction_rate": 0.03,
        "retrieval_precision": 0.85,
        "plan_success": 0.85,
        "policy_violation_count": 0.0,
        "regression_count": 0.0,
        "latency": 8.0,
        "compute_cost": 0.8,
        "rollback_count": 0.0,
        "improvement_survival": 1.0,
    }
    return _metrics(values)


def _metrics(values: dict[str, float]) -> tuple[BenchmarkMetric, ...]:
    thresholds = {
        "task_success": 0.8,
        "evidence_grounding": 0.8,
        "user_correction_rate": 0.05,
        "retrieval_precision": 0.75,
        "plan_success": 0.8,
        "policy_violation_count": 0.0,
        "regression_count": 0.0,
        "latency": 10.0,
        "compute_cost": 1.0,
        "rollback_count": 0.0,
        "improvement_survival": 1.0,
    }
    return tuple(
        BenchmarkMetric(
            metric_name=name,
            value=values[name],
            threshold=thresholds[name],
            higher_is_better=name in HIGHER_IS_BETTER_METRICS,
            unit="score" if name in HIGHER_IS_BETTER_METRICS else "count",
        )
        for name in REQUIRED_BENCHMARK_METRICS
    )


def _now() -> datetime:
    return datetime.now(UTC)
