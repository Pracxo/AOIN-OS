"""Brain loop execution reference tests."""

from datetime import UTC, datetime

from aion_brain.context.compiler import ContextCompiler, EmptyCapabilityCatalog
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.intent.engine import IntentEngine
from aion_brain.planning.planner import Planner
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter


class FakePolicyAdapter:
    """Policy fake for execution readiness tests."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


def test_brain_think_does_not_auto_execute() -> None:
    """Thinking advertises execution readiness but does not execute plans."""
    policy = FakePolicyAdapter()
    trace = LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy,
            capability_catalog=EmptyCapabilityCatalog(),
        ),
        planner=Planner(),
        policy_adapter=policy,
    ).run(make_event())

    assert trace.execution_refs == []
    assert trace.outcome["execution_ready"] is True
    assert trace.outcome["execution_endpoint"] == "/brain/execute"


def make_event() -> AIONEvent:
    """Create a generic event."""
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        actor_id="actor-1",
        workspace_id="workspace-1",
        payload_type="test.payload",
        payload={"question": "what should happen?"},
        timestamp=datetime.now(UTC),
        correlation_id="corr-1",
        trace_id="trace-1",
        security_scope=["workspace:main"],
    )
