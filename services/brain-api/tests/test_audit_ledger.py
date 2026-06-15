"""Audit ledger tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.audit.ledger import AuditLedger
from aion_brain.audit.repository import AuditRepository
from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.traces import DecisionTrace


def make_repository() -> AuditRepository:
    """Create an isolated audit repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return AuditRepository(engine=engine)


def make_trace() -> DecisionTrace:
    """Create a trace."""
    return DecisionTrace(
        trace_id="trace-1",
        event_id="event-1",
        intent_id="intent-1",
        context_id="context-1",
        plan_id="plan-1",
        memory_refs=["memory-1"],
        capability_refs=[],
        policy_decisions=["decision-1"],
        outcome={"status": "planned"},
        created_at=datetime.now(UTC),
    )


def test_audit_ledger_persists_trace_artifacts() -> None:
    """The audit ledger records and reads trace artifacts."""
    repository = make_repository()
    ledger = AuditLedger(repository)
    trace = make_trace()
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
        signal={"lesson": "generic"},
        confidence=0.8,
        promotion_status="candidate",
        created_at=datetime.now(UTC),
    )
    telemetry = VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        trace_id="trace-1",
        event_type="trace_created",
        node_type="trace",
        node_id="trace-1",
        edge_from=None,
        edge_to=None,
        intensity=0.9,
        payload={},
        created_at=datetime.now(UTC),
    )

    ledger.record(trace)
    ledger.record_policy_decisions(trace.trace_id, [decision])
    ledger.record_evaluation(evaluation)
    ledger.record_learning_signal(signal)
    ledger.record_visual_telemetry(trace.trace_id, [telemetry])

    assert repository.get_trace("trace-1") == trace
    assert repository.get_evaluation("trace-1") == evaluation
    assert repository.list_learning_signals("trace-1") == [signal]
    assert repository.list_visual_telemetry("trace-1") == [telemetry]
