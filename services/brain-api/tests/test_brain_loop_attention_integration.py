"""Brain loop attention integration tests."""

from datetime import UTC, datetime

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.planning import PlanGraph, PlanStep
from aion_brain.contracts.state import BrainState
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.learning.engine import LearningEngine
from aion_brain.telemetry.visual import VisualTelemetryBuilder


class FakeRuntime:
    def run_state(self, event: AIONEvent) -> BrainState:
        trace = DecisionTrace(
            trace_id=event.trace_id or "trace-1",
            event_id=event.event_id,
            intent_id="intent-1",
            context_id="context-1",
            plan_id="plan-1",
            memory_refs=[],
            capability_refs=[],
            reasoning_refs=["reasoning-1"],
            execution_refs=[],
            policy_decisions=[],
            outcome={"status": "planned"},
            created_at=datetime.now(UTC),
        )
        return BrainState(
            event=event,
            intent=IntentFrame(
                intent_id="intent-1",
                event_id=event.event_id,
                intent_type="question.answer",
                goal="answer",
                urgency="normal",
                risk_level="low",
                requires_memory=True,
                requires_capability=False,
                requires_approval=False,
                confidence=0.8,
            ),
            context=ContextPacket(
                context_id="context-1",
                intent_id="intent-1",
                goal="answer",
                known_context=[
                    {
                        "source": "attention_decision",
                        "attention_decision_id": "attention-1",
                        "focus_session_id": "focus-1",
                        "selected_slot_ids": ["slot-1"],
                    }
                ],
                retrieved_memory_ids=[],
                available_capability_ids=[],
                constraints=[],
                open_questions=[],
                execution_limits={},
            ),
            plan=PlanGraph(
                plan_id="plan-1",
                intent_id="intent-1",
                goal="answer",
                steps=[
                    PlanStep(
                        step_id="step-1",
                        action_type="response.draft",
                        capability_required=None,
                        risk_level="low",
                        status="pending",
                    )
                ],
                dependencies=[],
                risk_level="low",
                approval_required=False,
                status="planned",
            ),
            trace=trace,
            status="planned",
        )


class FakeAuditLedger:
    def record(self, trace):
        return trace

    def record_policy_decisions(self, trace_id, policy_decisions):
        return policy_decisions

    def record_evaluation(self, evaluation):
        return evaluation

    def record_learning_signal(self, learning_signal):
        return learning_signal

    def record_visual_telemetry(self, trace_id, telemetry_events):
        return telemetry_events


class FakeWorkingMemory:
    def __init__(self) -> None:
        self.requests = []

    def write_slot(self, request):
        self.requests.append(request)
        return request


class FakeAttentionController:
    def __init__(self) -> None:
        self.signals = []

    def create_signal(self, request):
        self.signals.append(request)
        return request


class FakeFocusService:
    def __init__(self) -> None:
        self.created = []

    def create_focus_session(self, request):
        self.created.append(request)
        return type("Focus", (), {"focus_session_id": "focus-created"})()


def test_brain_loop_writes_working_memory_and_attention_metadata() -> None:
    """Brain loop writes compact stage slots and attaches attention metadata."""
    working_memory = FakeWorkingMemory()
    attention = FakeAttentionController()
    focus = FakeFocusService()
    service = BrainLoopService(
        runtime=FakeRuntime(),
        audit_ledger=FakeAuditLedger(),
        evaluator=Evaluator(),
        learning_engine=LearningEngine(),
        telemetry_builder=VisualTelemetryBuilder(),
        focus_service=focus,
        attention_controller=attention,
        working_memory_service=working_memory,
    )

    state = service.run_full_loop(event())

    assert focus.created == []
    assert attention.signals
    assert {
        request.slot_type for request in working_memory.requests
    } >= {"recent_event", "retrieved_context", "reasoning_note", "plan_note"}
    assert state.trace.outcome["attention_decision_id"] == "attention-1"
    assert state.trace.outcome["focus_session_id"] == "focus-1"


def event() -> AIONEvent:
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        payload_type="test",
        payload={"question": "what now?"},
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
        correlation_id="corr-1",
        security_scope=["workspace:main"],
    )
