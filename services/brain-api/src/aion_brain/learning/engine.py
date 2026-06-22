"""Learning signal engine."""

from datetime import UTC, datetime

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal, LearningType
from aion_brain.contracts.traces import DecisionTrace


class LearningEngine:
    """Creates candidate learnings without self-modification."""

    def create_signal(
        self,
        *,
        trace: DecisionTrace,
        evaluation: EvaluationRecord,
    ) -> LearningSignal:
        """Create a deterministic candidate learning signal."""
        learning_type = _learning_type(trace, evaluation)
        confidence = _confidence(evaluation)
        return LearningSignal(
            learning_id=f"learning-{trace.trace_id}",
            trace_id=trace.trace_id,
            learning_type=learning_type,
            signal={
                "evaluation_id": evaluation.evaluation_id,
                "lessons": evaluation.lessons,
                "outcome_status": trace.outcome.get("status", "unknown"),
            },
            confidence=confidence,
            promotion_status="candidate",
            created_at=datetime.now(UTC),
        )

    def promote(self, signal: LearningSignal) -> LearningSignal:
        """Promotion is intentionally unavailable in v0.1."""
        raise NotImplementedError("Learning promotion is not implemented in v0.1.")


def _learning_type(trace: DecisionTrace, evaluation: EvaluationRecord) -> LearningType:
    status = trace.outcome.get("status")
    execution_status = trace.outcome.get("execution_status")
    task_run_status = trace.outcome.get("task_run_status")
    if task_run_status in {"failed", "blocked_by_policy"}:
        return "failure_pattern_candidate"
    if trace.outcome.get("repeated_task_pattern") is True:
        return "planning_pattern_candidate"
    if execution_status in {"failed", "blocked_by_policy"}:
        return "failure_pattern_candidate"
    if execution_status == "completed":
        return "planning_pattern_candidate"
    if status == "blocked_by_policy":
        return "policy_feedback_candidate"
    if evaluation.scores.get("memory_relevance_score", 0.0) < 0.7:
        return "retrieval_improvement_candidate"
    if evaluation.scores.get("plan_quality_score", 0.0) < 0.7:
        return "planning_pattern_candidate"
    if not trace.capability_refs:
        return "capability_selection_candidate"
    return "planning_pattern_candidate"


def _confidence(evaluation: EvaluationRecord) -> float:
    if not evaluation.scores:
        return 0.5
    return max(0.0, min(1.0, sum(evaluation.scores.values()) / len(evaluation.scores)))
