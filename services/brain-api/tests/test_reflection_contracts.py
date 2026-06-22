"""Reflection contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.reflection import ReflectionRecord, ReflectionRequest
from aion_brain.contracts.traces import DecisionTrace


def test_reflection_record_validates_confidence_bounds() -> None:
    """Reflection confidence is bounded from 0 to 1."""
    with pytest.raises(ValidationError):
        ReflectionRecord(
            reflection_id="reflection-1",
            reflection_type="trace_review",
            observations=["observed"],
            confidence=1.2,
            status="recorded",
        )


def test_reflection_record_requires_observations_unless_dismissed() -> None:
    """Only dismissed reflections may have empty observations."""
    with pytest.raises(ValidationError):
        ReflectionRecord(
            reflection_id="reflection-1",
            reflection_type="trace_review",
            observations=[],
            confidence=0.5,
            status="recorded",
        )

    dismissed = ReflectionRecord(
        reflection_id="reflection-1",
        reflection_type="trace_review",
        observations=[],
        confidence=0.5,
        status="dismissed",
    )

    assert dismissed.status == "dismissed"


def test_reflection_request_accepts_trace_and_evaluation() -> None:
    """ReflectionRequest accepts evaluated Brain trace inputs."""
    request = ReflectionRequest(
        trace=make_trace(),
        evaluation=make_evaluation(),
        reflection_type="trace_review",
    )

    assert request.trace is not None
    assert request.evaluation is not None


def make_trace() -> DecisionTrace:
    """Create a decision trace."""
    return DecisionTrace(
        trace_id="trace-1",
        event_id="event-1",
        intent_id="intent-1",
        context_id="context-1",
        plan_id="plan-1",
        memory_refs=[],
        capability_refs=[],
        policy_decisions=[],
        outcome={"status": "planned"},
        created_at=datetime.now(UTC),
    )


def make_evaluation() -> EvaluationRecord:
    """Create an evaluation record."""
    return EvaluationRecord(
        evaluation_id="evaluation-1",
        trace_id="trace-1",
        scores={"plan_quality_score": 0.7},
        lessons=[],
        created_at=datetime.now(UTC),
    )
