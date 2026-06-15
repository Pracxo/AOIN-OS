"""Visual telemetry tests for reflection and skill events."""

from datetime import UTC, datetime

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.telemetry.visual import VisualTelemetryBuilder


def test_visual_telemetry_emits_reflection_and_skill_candidate_events() -> None:
    """Trace outcome reflection/candidate IDs become graph telemetry."""
    events = VisualTelemetryBuilder().build(
        trace=DecisionTrace(
            trace_id="trace-1",
            event_id="event-1",
            intent_id=None,
            context_id=None,
            plan_id=None,
            memory_refs=[],
            capability_refs=[],
            policy_decisions=[],
            outcome={
                "status": "planned",
                "reflection_id": "reflection-1",
                "candidate_id": "candidate-1",
            },
            created_at=datetime.now(UTC),
        ),
        policy_decisions=[],
        evaluation=EvaluationRecord(
            evaluation_id="evaluation-1",
            trace_id="trace-1",
            scores={"plan_quality_score": 0.8},
            lessons=[],
            created_at=datetime.now(UTC),
        ),
        learning_signal=LearningSignal(
            learning_id="learning-1",
            trace_id="trace-1",
            learning_type="planning_pattern_candidate",
            signal={},
            confidence=0.8,
            promotion_status="candidate",
            created_at=datetime.now(UTC),
        ),
    )

    assert {event.event_type for event in events} >= {
        "reflection_created",
        "skill_candidate_created",
    }
