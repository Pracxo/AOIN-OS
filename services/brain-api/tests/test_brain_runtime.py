"""Brain runtime tests."""

from datetime import UTC, datetime

from aion_brain.context.compiler import ContextCompiler, EmptyCapabilityCatalog
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.intent.engine import IntentEngine
from aion_brain.planning.planner import Planner
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter


class FakePolicyAdapter:
    """Policy adapter fake for runtime tests."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allowed = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allowed,
            approval_required=not allowed,
            reason="allowed" if allowed else "denied",
            constraints=[] if allowed else ["blocked"],
            audit_level="standard" if allowed else "high",
        )


class NoExecutionCapabilityCatalog(EmptyCapabilityCatalog):
    """Catalog fake that fails if invocation is accidentally attempted."""

    def invoke(self, capability_id: str, payload: dict[str, object]) -> dict[str, object]:
        raise AssertionError("capability execution must not happen in AION-008")


def make_event(event_type: str = "question.answer") -> AIONEvent:
    """Create a generic event."""
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type=event_type,
        actor_id="actor-1",
        workspace_id="workspace-1",
        payload_type="test.payload",
        payload={"question": "what should happen?"},
        timestamp=datetime.now(UTC),
        correlation_id="corr-1",
        trace_id="trace-1",
        security_scope=["workspace:main"],
    )


def make_runtime(policy: FakePolicyAdapter) -> LangGraphRuntimeAdapter:
    """Create a deterministic runtime with fake dependencies."""
    return LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy,
            capability_catalog=NoExecutionCapabilityCatalog(),
        ),
        planner=Planner(),
        policy_adapter=policy,
    )


def test_langgraph_runtime_returns_public_decision_trace() -> None:
    """The runtime returns only the public AION DecisionTrace contract."""
    policy = FakePolicyAdapter()

    trace = make_runtime(policy).run(make_event())

    assert isinstance(trace, DecisionTrace)
    assert trace.outcome["status"] == "planned"
    assert trace.outcome["runtime"] == "langgraph"
    assert trace.intent_id == "intent-event-1"
    assert trace.context_id == "context-event-1"
    assert trace.plan_id == "plan-intent-event-1"
    assert [request.action_type for request in policy.requests] == [
        "context.compile",
            "memory.retrieve",
            "memory.retrieve",
            "memory.retrieve",
            "memory.retrieve",
            "evidence.search",
            "capability.list",
            "reasoning.run",
            "model.route",
        "model.complete",
        "plan.create",
        "memory.retrieve",
        "response.draft",
        "evaluation.score",
        "plan.execute",
    ]


def test_langgraph_runtime_blocks_when_policy_denies_plan() -> None:
    """Policy denial creates a blocked trace instead of execution."""
    policy = FakePolicyAdapter(deny_action="plan.create")

    trace = make_runtime(policy).run(make_event("goal.plan"))

    assert trace.outcome["status"] == "blocked_by_policy"
    assert trace.policy_decisions[-1] == "decision-7"


def test_langgraph_runtime_does_not_execute_capabilities() -> None:
    """Capability invocation is not part of the deterministic runtime."""
    policy = FakePolicyAdapter()

    trace = make_runtime(policy).run(make_event("capability.discover"))

    assert trace.outcome["status"] == "planned"
    assert "capability.invoke" not in [request.action_type for request in policy.requests]
