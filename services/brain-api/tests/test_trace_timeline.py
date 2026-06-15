"""Trace timeline builder tests."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.audit.repository import AuditRepository
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.contracts.visual import TraceTimelineRequest
from aion_brain.visual.repository import VisualRepository
from aion_brain.visual.timeline import TraceTimelineBuilder
from tests.test_visual_service import telemetry


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


def test_trace_timeline_builder_orders_events_and_handles_missing_sections() -> None:
    """Timeline projection is ordered and tolerates absent optional artifacts."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    audit = AuditRepository(engine=engine)
    visual = VisualRepository(engine=engine)
    now = datetime.now(UTC)
    trace = DecisionTrace(
        trace_id="trace-1",
        event_id="event-1",
        intent_id=None,
        context_id=None,
        plan_id=None,
        memory_refs=[],
        capability_refs=[],
        reasoning_refs=[],
        execution_refs=[],
        policy_decisions=[],
        outcome={"status": "planned"},
        created_at=now,
    )
    audit.save_trace(trace)
    item = telemetry().model_copy(update={"created_at": now + timedelta(seconds=1)})
    audit.save_visual_telemetry("trace-1", [item])

    timeline = TraceTimelineBuilder(audit, visual, AllowPolicy()).build(
        TraceTimelineRequest(trace_id="trace-1", scope=["workspace:main"])
    )

    assert [event.timestamp for event in timeline.events] == sorted(
        event.timestamp for event in timeline.events
    )
    assert timeline.duration_ms == 1000
