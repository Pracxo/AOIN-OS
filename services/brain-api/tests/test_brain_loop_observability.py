"""Brain loop observability integration tests."""

from aion_brain.context.compiler import ContextCompiler, EmptyCapabilityCatalog
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.intent.engine import IntentEngine
from aion_brain.learning.engine import LearningEngine
from aion_brain.planning.planner import Planner
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter
from aion_brain.telemetry.visual import VisualTelemetryBuilder
from tests.test_brain_loop_reasoning import FakePolicyAdapter, make_event


class FakeAuditLedger:
    """No-op audit ledger fake."""

    def record(self, trace):
        return trace.trace_id

    def record_policy_decisions(self, trace_id, decisions):
        return decisions

    def record_evaluation(self, evaluation):
        return evaluation

    def record_learning_signal(self, signal):
        return signal

    def record_visual_telemetry(self, trace_id, events):
        return events


class FakeRecorder:
    """Observability recorder fake."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.events = []

    def record_event(self, event):
        if self.fail:
            raise RuntimeError("recorder unavailable")
        self.events.append(event)
        return event

    def summarize(self, scope):
        raise NotImplementedError


def test_brain_think_records_observability_events() -> None:
    """The deterministic loop records its key local observability stages."""
    recorder = FakeRecorder()
    trace = make_service(recorder).think(make_event())

    assert trace.trace_id == "trace-1"
    assert {event.event_type for event in recorder.events} >= {
        "brain_loop_started",
        "intent_classified",
        "context_compiled",
        "plan_created",
        "policy_checked",
        "trace_created",
        "evaluation_completed",
        "learning_signal_created",
        "brain_loop_completed",
    }


def test_observability_failure_does_not_break_brain_loop() -> None:
    """Recorder failures never break Brain reasoning and planning."""
    trace = make_service(FakeRecorder(fail=True)).think(make_event())
    assert trace.outcome["status"] == "planned"


def make_service(recorder: FakeRecorder) -> BrainLoopService:
    policy = FakePolicyAdapter()
    runtime = LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy,
            capability_catalog=EmptyCapabilityCatalog(),
        ),
        planner=Planner(),
        policy_adapter=policy,
    )
    return BrainLoopService(
        runtime=runtime,
        audit_ledger=FakeAuditLedger(),  # type: ignore[arg-type]
        evaluator=Evaluator(),
        learning_engine=LearningEngine(),
        telemetry_builder=VisualTelemetryBuilder(),
        observability_adapter=recorder,  # type: ignore[arg-type]
    )
