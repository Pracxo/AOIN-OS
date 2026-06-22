"""Brain loop reasoning integration tests."""

from datetime import UTC, datetime

from aion_brain.context.compiler import ContextCompiler, EmptyCapabilityCatalog
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.intent.engine import IntentEngine
from aion_brain.planning.planner import Planner
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter


class FakePolicyAdapter:
    """Policy fake for Brain loop reasoning tests."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        allowed = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=allowed,
            approval_required=not allowed,
            reason="allowed" if allowed else "denied",
            constraints=[] if allowed else ["blocked"],
            audit_level="standard" if allowed else "high",
        )


def test_brain_loop_trace_includes_reasoning_refs() -> None:
    """POST /brain/think flow adds reasoning references to traces."""
    trace = make_runtime(FakePolicyAdapter()).run(make_event())

    assert trace.reasoning_refs == ["reasoning-event-1"]
    assert trace.outcome["reasoning"] == "deterministic-local"
    assert trace.outcome["message"] == (
        "AION Brain completed deterministic reasoning and planning loop."
    )


def test_brain_loop_policy_deny_blocks_reasoning() -> None:
    """Reasoning policy denial blocks the loop before planning."""
    trace = make_runtime(FakePolicyAdapter(deny_action="reasoning.run")).run(make_event())

    assert trace.outcome["status"] == "blocked_by_policy"
    assert trace.plan_id is None
    assert trace.reasoning_refs == ["reasoning-event-1"]


def make_runtime(policy: FakePolicyAdapter) -> LangGraphRuntimeAdapter:
    """Create a runtime with fake dependencies."""
    return LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy,
            capability_catalog=EmptyCapabilityCatalog(),
        ),
        planner=Planner(),
        policy_adapter=policy,
    )


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
