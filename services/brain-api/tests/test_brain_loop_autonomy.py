"""Brain loop autonomy integration tests."""

from aion_brain.context.compiler import ContextCompiler, EmptyCapabilityCatalog
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.intent.engine import IntentEngine
from aion_brain.learning.engine import LearningEngine
from aion_brain.planning.planner import Planner
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter
from aion_brain.telemetry.visual import VisualTelemetryBuilder
from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_brain_loop_observability import FakeAuditLedger
from tests.test_brain_loop_reasoning import FakePolicyAdapter, make_event


def test_brain_loop_returns_policy_blocked_trace_when_autonomy_denies() -> None:
    """The full Brain loop stops before reasoning when autonomy denies thinking."""
    service = make_service(FakeAutonomyGovernor(allow=False))

    state = service.run_full_loop(make_event())

    assert state.status == "blocked_by_autonomy"
    assert state.intent is None
    assert state.context is None
    assert state.plan is None
    assert state.trace.outcome["autonomy_decision_id"] == "autonomy-decision-1"


def test_brain_loop_observe_mode_does_not_plan() -> None:
    """Observe mode records an observed trace without planning."""
    service = make_service(FakeAutonomyGovernor(allow=True, resolved_mode="observe"))

    trace = service.think(make_event())

    assert trace.outcome["status"] == "observed"
    assert trace.plan_id is None


def make_service(autonomy: FakeAutonomyGovernor) -> BrainLoopService:
    """Create a BrainLoopService with deterministic runtime and fake autonomy."""
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
        autonomy_governor=autonomy,
    )
