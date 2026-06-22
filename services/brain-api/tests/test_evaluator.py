"""Evaluator tests."""

from datetime import UTC, datetime

from aion_brain.contracts.traces import DecisionTrace
from aion_brain.evaluation.evaluator import Evaluator


def make_trace(*, status: str = "planned", plan_id: str | None = "plan-1") -> DecisionTrace:
    """Create a trace for evaluator tests."""
    return DecisionTrace(
        trace_id="trace-1",
        event_id="event-1",
        intent_id="intent-1",
        context_id="context-1",
        plan_id=plan_id,
        memory_refs=[],
        capability_refs=[],
        policy_decisions=["decision-1"],
        outcome={"status": status},
        created_at=datetime.now(UTC),
    )


def test_evaluator_scores_are_bounded() -> None:
    """Every deterministic score is between 0 and 1."""
    evaluation = Evaluator().evaluate(make_trace())

    assert all(0.0 <= score <= 1.0 for score in evaluation.scores.values())
    assert evaluation.trace_id == "trace-1"
    assert "reasoning_quality_score" in evaluation.scores
    assert "execution_readiness_score" in evaluation.scores


def test_blocked_by_policy_keeps_policy_compliance_high() -> None:
    """Correct policy blocks are treated as compliant."""
    evaluation = Evaluator().evaluate(make_trace(status="blocked_by_policy"))

    assert evaluation.scores["policy_compliance_score"] >= 0.9
    assert "policy_block_was_preserved" in evaluation.lessons


def test_missing_plan_lowers_plan_quality() -> None:
    """A plan-capable trace without a plan has low plan quality."""
    evaluation = Evaluator().evaluate(make_trace(plan_id=None))

    assert evaluation.scores["plan_quality_score"] < 0.5


def test_reasoning_quality_scores_confident_reasoning() -> None:
    """Confident reasoning with no clarification receives a full reasoning score."""
    trace = make_trace()
    trace = trace.model_copy(
        update={
            "reasoning_refs": ["reasoning-1"],
            "outcome": {
                "status": "planned",
                "reasoning_confidence": 0.85,
                "reasoning_requires_clarification": False,
            },
        }
    )

    evaluation = Evaluator().evaluate(trace)

    assert evaluation.scores["reasoning_quality_score"] == 1.0


def test_execution_readiness_scores_policy_allowed_plan() -> None:
    """Execution readiness is full when dry-run execution is policy-ready."""
    trace = make_trace().model_copy(
        update={"outcome": {"status": "planned", "execution_ready": True}}
    )

    evaluation = Evaluator().evaluate(trace)

    assert evaluation.scores["execution_readiness_score"] == 1.0
