"""CapabilityInvoker runtime gateway integration tests."""

from datetime import UTC, datetime

from aion_brain.contracts.modules import CapabilityInvocationRequest, CapabilityInvocationResult
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.execution.capability_invoker import CapabilityInvoker


class FakePolicyAdapter:
    """Policy fake."""

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


class FakeRuntimeGateway:
    """Runtime gateway fake."""

    def __init__(self) -> None:
        self.requests: list[CapabilityInvocationRequest] = []

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityInvocationResult:
        self.requests.append(request)
        return CapabilityInvocationResult(
            invocation_id=request.invocation_id,
            capability_id=request.capability_id,
            runtime_id="runtime-1",
            status="completed",
            output={"executed": True},
            error={},
            policy_decision_id="decision-1",
            latency_ms=0,
            created_at=datetime.now(UTC),
        )


def test_capability_invoker_uses_runtime_gateway() -> None:
    """CapabilityInvoker delegates configured invocations to the runtime gateway."""
    gateway = FakeRuntimeGateway()
    record = CapabilityInvoker(
        policy_adapter=FakePolicyAdapter(),
        runtime_gateway=gateway,  # type: ignore[arg-type]
    ).invoke(
        "aion.internal.noop",
        {"mode": "controlled", "execution_id": "execution-1", "step_run_id": "step-1"},
        "execution-1",
        "step-1",
        "trace-1",
    )

    assert gateway.requests[0].capability_id == "aion.internal.noop"
    assert gateway.requests[0].mode == "controlled"
    assert record.status == "completed"
    assert record.output["gateway_status"] == "completed"
