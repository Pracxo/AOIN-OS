"""Visual telemetry tests."""

from datetime import UTC, datetime

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.telemetry.visual import VisualTelemetryBuilder, build_graph_memory_activation_event


def test_visual_telemetry_uses_allowed_event_types() -> None:
    """Telemetry events are valid AION visual telemetry contracts."""
    trace = DecisionTrace(
        trace_id="trace-1",
        event_id="event-1",
        intent_id="intent-1",
        context_id="context-1",
        plan_id="plan-1",
        memory_refs=["memory-1"],
        capability_refs=[],
        execution_refs=["execution-1"],
        policy_decisions=["decision-1"],
        outcome={"status": "planned", "execution_status": "completed"},
        created_at=datetime.now(UTC),
    )
    decision = PolicyDecision(
        decision_id="decision-1",
        trace_id="trace-1",
        allow=True,
        approval_required=False,
        reason="allowed",
        constraints=[],
        audit_level="standard",
    )
    evaluation = EvaluationRecord(
        evaluation_id="evaluation-trace-1",
        trace_id="trace-1",
        scores={"goal_completion_score": 0.8},
        lessons=["deterministic_loop_completed"],
        created_at=datetime.now(UTC),
    )
    signal = LearningSignal(
        learning_id="learning-trace-1",
        trace_id="trace-1",
        learning_type="planning_pattern_candidate",
        signal={},
        confidence=0.8,
        promotion_status="candidate",
        created_at=datetime.now(UTC),
    )

    events = VisualTelemetryBuilder().build(
        trace=trace,
        policy_decisions=[decision],
        evaluation=evaluation,
        learning_signal=signal,
    )

    event_types = {event.event_type for event in events}
    assert "brain_loop_started" in event_types
    assert "trace_created" in event_types
    assert "execution_started" in event_types
    assert "execution_completed" in event_types
    assert "evaluation_completed" in event_types
    assert "learning_signal_created" in event_types
    assert all(0.0 <= event.intensity <= 1.0 for event in events)


def test_visual_telemetry_emits_graph_memory_activation_events() -> None:
    """Graph memory activation uses the future Brain map telemetry contract."""
    event = build_graph_memory_activation_event(
        object_id="node-1",
        intensity=0.75,
        payload={"object_type": "node"},
    )

    assert event.event_type == "memory_node_activated"
    assert event.node_type == "memory"
    assert event.node_id == "node-1"
    assert event.intensity == 0.75
