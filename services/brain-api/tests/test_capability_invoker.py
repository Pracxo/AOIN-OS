"""CapabilityInvoker tests."""

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.execution.capability_invoker import CapabilityInvoker


class FakePolicyAdapter:
    """Policy fake for capability invoker tests."""

    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard" if self.allow else "high",
        )


def test_capability_invoker_returns_not_implemented_for_existing_capability() -> None:
    """Existing capabilities are not executed in v0.1."""
    registry = CapabilityRegistry()
    registry.register(make_manifest())
    record = CapabilityInvoker(
        capability_registry=registry,
        policy_adapter=FakePolicyAdapter(),
    ).invoke("test.echo", {}, "execution-1", "step-1", "trace-1")

    assert record.status == "not_implemented"
    assert record.output["invoked"] is False


def test_capability_invoker_returns_failed_for_missing_capability() -> None:
    """Missing capabilities return a structured failed record."""
    record = CapabilityInvoker(
        capability_registry=CapabilityRegistry(),
        policy_adapter=FakePolicyAdapter(),
    ).invoke("missing", {}, "execution-1", "step-1", "trace-1")

    assert record.status == "failed"
    assert record.output["reason"] == "capability_not_found"


def test_capability_invoker_policy_deny_returns_blocked() -> None:
    """Policy denial blocks capability invocation."""
    registry = CapabilityRegistry()
    registry.register(make_manifest())
    record = CapabilityInvoker(
        capability_registry=registry,
        policy_adapter=FakePolicyAdapter(allow=False),
    ).invoke("test.echo", {}, "execution-1", "step-1", "trace-1")

    assert record.status == "blocked_by_policy"
    assert record.policy_decision_id == "decision-capability.invoke"


def make_manifest() -> CapabilityManifest:
    """Create a generic capability manifest."""
    return CapabilityManifest(
        module_id="test.module",
        version="0.1.0",
        capabilities=[{"capability_id": "test.echo", "name": "Echo"}],
        permissions_required=[],
        memory_read_scopes=[],
        memory_write_scopes=[],
        events_subscribed=[],
        events_published=[],
        execution_mode="sync",
    )
