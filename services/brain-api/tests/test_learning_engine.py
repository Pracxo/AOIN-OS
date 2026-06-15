"""Learning engine tests."""

from datetime import UTC, datetime

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.learning.engine import LearningEngine


def make_trace(status: str = "planned") -> DecisionTrace:
    """Create a trace."""
    return DecisionTrace(
        trace_id="trace-1",
        event_id="event-1",
        intent_id="intent-1",
        context_id="context-1",
        plan_id="plan-1",
        memory_refs=[],
        capability_refs=[],
        policy_decisions=["decision-1"],
        outcome={"status": status},
        created_at=datetime.now(UTC),
    )


def make_evaluation() -> EvaluationRecord:
    """Create an evaluation."""
    return EvaluationRecord(
        evaluation_id="evaluation-trace-1",
        trace_id="trace-1",
        scores={
            "goal_completion_score": 0.8,
            "context_quality_score": 0.8,
            "memory_relevance_score": 0.6,
        },
        lessons=["memory_recall_was_empty"],
        created_at=datetime.now(UTC),
    )


def test_learning_signal_stays_candidate() -> None:
    """Learning signals are candidates and never auto-promoted."""
    signal = LearningEngine().create_signal(trace=make_trace(), evaluation=make_evaluation())

    assert signal.promotion_status == "candidate"
    assert signal.learning_type == "retrieval_improvement_candidate"
    assert 0.0 <= signal.confidence <= 1.0


def test_policy_block_creates_policy_feedback_candidate() -> None:
    """Policy blocks create generic policy feedback candidates."""
    signal = LearningEngine().create_signal(
        trace=make_trace(status="blocked_by_policy"),
        evaluation=make_evaluation(),
    )

    assert signal.learning_type == "policy_feedback_candidate"


def test_execution_failure_creates_failure_pattern_candidate() -> None:
    """Execution failures create generic failure learning candidates."""
    trace = make_trace().model_copy(
        update={"outcome": {"status": "planned", "execution_status": "failed"}}
    )

    signal = LearningEngine().create_signal(trace=trace, evaluation=make_evaluation())

    assert signal.learning_type == "failure_pattern_candidate"
