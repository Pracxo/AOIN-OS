"""Proposal service for the AION-170 improvement experiment engine."""

from __future__ import annotations

from collections.abc import Iterable

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.experience import ExperienceRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.learning_synthesis import (
    LearningPattern,
    LearningSynthesisRun,
    LessonRecord,
    RegressionCandidateSuggestion,
    SkillCandidateSuggestion,
)
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.contracts.skills import SkillCandidate
from aion_brain.self_improvement.benchmark_contracts import BenchmarkMetric
from aion_brain.self_improvement.experiment import (
    ImprovementEvidenceBundle,
    ImprovementExperimentPlan,
    ImprovementExperimentResult,
    ImprovementProposal,
    ProposalLifecycleState,
)
from aion_brain.self_improvement.experiment_runner import ImprovementExperimentRunner
from aion_brain.self_improvement.hypothesis import (
    DisabledHypothesisGenerator,
    HypothesisGenerator,
    ImprovementChangeType,
)
from aion_brain.self_improvement.observation import (
    ImprovementObservation,
    observation_from_evaluation_record,
)
from aion_brain.self_improvement.pattern_intake import (
    ImprovementFailurePattern,
    intake_failure_pattern,
)
from aion_brain.self_improvement.regression_proposal import (
    DisabledRegressionTestProposalGenerator,
    RegressionTestProposal,
    RegressionTestProposalGenerator,
)


class ImprovementProposalService:
    """Build approval-pending proposals without source, Git, PR, or runtime effects."""

    def __init__(
        self,
        *,
        hypothesis_generator: HypothesisGenerator | None = None,
        regression_test_generator: RegressionTestProposalGenerator | None = None,
        experiment_runner: ImprovementExperimentRunner | None = None,
    ) -> None:
        self._hypothesis_generator = hypothesis_generator or DisabledHypothesisGenerator()
        self._regression_test_generator = (
            regression_test_generator or DisabledRegressionTestProposalGenerator()
        )
        self._experiment_runner = experiment_runner or ImprovementExperimentRunner()

    def build_approval_pending_bundle(
        self,
        *,
        proposal_id: str,
        author_actor_id: str,
        evaluation_records: Iterable[EvaluationRecord],
        baseline_metrics: tuple[BenchmarkMetric, ...],
        target_metrics: tuple[BenchmarkMetric, ...],
        learning_signals: Iterable[LearningSignal] = (),
        learning_patterns: Iterable[LearningPattern] = (),
        learning_synthesis_runs: Iterable[LearningSynthesisRun] = (),
        experiences: Iterable[ExperienceRecord] = (),
        lessons: Iterable[LessonRecord] = (),
        skill_candidates: Iterable[SkillCandidate] = (),
        skill_candidate_suggestions: Iterable[SkillCandidateSuggestion] = (),
        regression_suggestions: Iterable[RegressionCandidateSuggestion] = (),
        candidate_metrics: tuple[BenchmarkMetric, ...] | None = None,
        min_frequency: int = 2,
    ) -> ImprovementEvidenceBundle:
        """Run the full AION-170 proposal flow and return an evidence bundle."""

        synthesis_runs = tuple(learning_synthesis_runs)
        observations = _observations_from_evaluations(evaluation_records)
        all_learning_patterns = (*tuple(learning_patterns), *_patterns_from_runs(synthesis_runs))
        all_experiences = (*tuple(experiences), *_experiences_from_runs(synthesis_runs))
        all_lessons = (*tuple(lessons), *_lessons_from_runs(synthesis_runs))
        all_skill_suggestions = (
            *tuple(skill_candidate_suggestions),
            *_skill_suggestions_from_runs(synthesis_runs),
        )
        all_regression_suggestions = (
            *tuple(regression_suggestions),
            *_regression_suggestions_from_runs(synthesis_runs),
        )
        failure_pattern = intake_failure_pattern(
            failure_pattern_id=f"failure-pattern-{proposal_id}",
            observations=observations,
            learning_patterns=all_learning_patterns,
            experiences=all_experiences,
            min_frequency=min_frequency,
        )
        hypothesis = self._hypothesis_generator.generate(failure_pattern)
        regression_test_proposal = self._regression_test_generator.generate(hypothesis)
        experiment_plan = ImprovementExperimentPlan(
            experiment_plan_id=f"experiment-plan-{proposal_id}",
            failure_pattern_id=failure_pattern.failure_pattern_id,
            hypothesis_id=hypothesis.hypothesis_id,
            regression_test_proposal_id=(
                regression_test_proposal.regression_test_proposal_id
            ),
            baseline_metrics=baseline_metrics,
            target_metrics=target_metrics,
            candidate_slot_id=f"candidate-slot-{proposal_id}",
            allowed_paths=hypothesis.allowed_paths,
            prohibited_paths=hypothesis.prohibited_paths,
            experiment_spec={
                "baseline_run": "read_only",
                "candidate_slot": "metric_only",
                "source_mutation_enabled": False,
                "git_branch_created": False,
                "pr_created": False,
                "runtime_effect": False,
            },
            source_evidence_refs=hypothesis.source_evidence_refs,
            created_at=utc_now(),
        )
        experiment_result = self._experiment_runner.run(
            experiment_plan,
            experiment_result_id=f"experiment-result-{proposal_id}",
            candidate_metrics=candidate_metrics,
        )
        proposal = _proposal_from_result(
            proposal_id=proposal_id,
            author_actor_id=author_actor_id,
            failure_pattern=failure_pattern,
            experiment_plan=experiment_plan,
            experiment_result=experiment_result,
            baseline_metrics=baseline_metrics,
            target_metrics=target_metrics,
            rollback_requirement=experiment_result.risk_level in {"high", "critical"},
            test_specification=regression_test_proposal,
            change_type=hypothesis.change_type,
        )
        return ImprovementEvidenceBundle(
            evidence_bundle_id=f"evidence-bundle-{proposal_id}",
            observation_ids=tuple(item.observation_id for item in observations),
            failure_pattern=failure_pattern,
            hypothesis=hypothesis,
            regression_test_proposal=regression_test_proposal,
            experiment_plan=experiment_plan,
            experiment_result=experiment_result,
            proposal=proposal,
            evaluator_refs=tuple(
                f"evaluation:{record.evaluation_id}:trace:{record.trace_id}"
                for record in evaluation_records
            ),
            learning_signal_refs=tuple(
                f"learning-signal:{signal.learning_id}:{signal.learning_type}"
                for signal in learning_signals
            ),
            learning_pattern_refs=tuple(
                f"learning-pattern:{pattern.pattern_id}" for pattern in all_learning_patterns
            ),
            experience_refs=tuple(f"experience:{item.experience_id}" for item in all_experiences),
            lesson_refs=tuple(f"lesson:{item.lesson_id}" for item in all_lessons),
            skill_candidate_refs=(
                *tuple(f"skill-candidate:{item.candidate_id}" for item in skill_candidates),
                *tuple(
                    f"skill-suggestion:{item.suggestion_id}" for item in all_skill_suggestions
                ),
            ),
            regression_suggestion_refs=tuple(
                f"regression-suggestion:{item.regression_suggestion_id}"
                for item in all_regression_suggestions
            ),
            created_at=utc_now(),
        )


def _observations_from_evaluations(
    evaluation_records: Iterable[EvaluationRecord],
) -> tuple[ImprovementObservation, ...]:
    records = tuple(evaluation_records)
    if not records:
        raise ValueError("proposal service requires at least one evaluation record")
    return tuple(
        observation_from_evaluation_record(
            record,
            observation_id=f"observation-{index}-{record.evaluation_id}",
        )
        for index, record in enumerate(records, start=1)
    )


def _proposal_from_result(
    *,
    proposal_id: str,
    author_actor_id: str,
    failure_pattern: ImprovementFailurePattern,
    experiment_plan: ImprovementExperimentPlan,
    experiment_result: ImprovementExperimentResult,
    baseline_metrics: tuple[BenchmarkMetric, ...],
    target_metrics: tuple[BenchmarkMetric, ...],
    rollback_requirement: bool,
    test_specification: RegressionTestProposal,
    change_type: ImprovementChangeType,
) -> ImprovementProposal:
    risk_level = experiment_result.risk_level
    if risk_level not in {"low", "medium", "high", "critical"}:
        raise ValueError("invalid risk level")
    lifecycle_state: ProposalLifecycleState = (
        "approval_pending" if experiment_result.experiment_success else "blocked"
    )
    return ImprovementProposal(
        proposal_id=proposal_id,
        author_actor_id=author_actor_id,
        problem_statement=failure_pattern.problem_statement,
        source_evidence_refs=failure_pattern.source_evidence_refs,
        failure_pattern_id=failure_pattern.failure_pattern_id,
        baseline_metrics=baseline_metrics,
        target_metrics=target_metrics,
        change_type=change_type,
        allowed_paths=experiment_plan.allowed_paths,
        prohibited_paths=experiment_plan.prohibited_paths,
        test_specification=test_specification,
        experiment_specification=experiment_plan,
        risk_level=risk_level,
        approval_tier=experiment_result.approval_tier,
        rollback_requirement=rollback_requirement,
        lifecycle_state=lifecycle_state,
        created_at=utc_now(),
    )


def _patterns_from_runs(runs: tuple[LearningSynthesisRun, ...]) -> tuple[LearningPattern, ...]:
    return tuple(pattern for run in runs for pattern in run.patterns)


def _experiences_from_runs(runs: tuple[LearningSynthesisRun, ...]) -> tuple[ExperienceRecord, ...]:
    return tuple(experience for run in runs for experience in run.experiences)


def _lessons_from_runs(runs: tuple[LearningSynthesisRun, ...]) -> tuple[LessonRecord, ...]:
    return tuple(lesson for run in runs for lesson in run.lessons)


def _skill_suggestions_from_runs(
    runs: tuple[LearningSynthesisRun, ...],
) -> tuple[SkillCandidateSuggestion, ...]:
    return tuple(suggestion for run in runs for suggestion in run.skill_candidate_suggestions)


def _regression_suggestions_from_runs(
    runs: tuple[LearningSynthesisRun, ...],
) -> tuple[RegressionCandidateSuggestion, ...]:
    return tuple(suggestion for run in runs for suggestion in run.regression_candidate_suggestions)


__all__ = ["ImprovementProposalService"]
