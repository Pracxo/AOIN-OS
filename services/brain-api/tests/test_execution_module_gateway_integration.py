"""Execution integration with capability runtime gateway."""

from datetime import UTC, datetime

from aion_brain.contracts.execution import (
    ApprovalCheckpoint,
    CapabilityInvocationRecord,
    ExecutionRequest,
    ExecutionRun,
    ExecutionStepRun,
)
from aion_brain.contracts.modules import CapabilityInvocationRequest, CapabilityInvocationResult
from aion_brain.contracts.planning import PlanGraph, PlanStep
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.execution.capability_invoker import CapabilityInvoker
from aion_brain.execution.orchestrator import ExecutionOrchestrator


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


class FakeRepository:
    """Execution repository fake."""

    def save_execution(self, run: ExecutionRun) -> ExecutionRun:
        return run

    def save_step(self, step: ExecutionStepRun) -> ExecutionStepRun:
        return step

    def save_approval(self, approval: ApprovalCheckpoint) -> ApprovalCheckpoint:
        return approval

    def save_capability_invocation(
        self,
        record: CapabilityInvocationRecord,
    ) -> CapabilityInvocationRecord:
        return record


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
            policy_decision_id="decision-runtime",
            latency_ms=0,
            created_at=datetime.now(UTC),
        )


def test_execution_controlled_mode_invokes_gateway_indirectly() -> None:
    """Controlled execution invokes capability through CapabilityInvoker and gateway."""
    gateway = FakeRuntimeGateway()
    invoker = CapabilityInvoker(
        policy_adapter=FakePolicyAdapter(),
        runtime_gateway=gateway,  # type: ignore[arg-type]
    )
    run = make_orchestrator(invoker=invoker).execute(
        make_request(plan=make_plan([capability_step()]), mode="controlled")
    )

    assert run.status == "completed"
    assert gateway.requests[0].mode == "controlled"
    assert run.capability_invocations[0].output["gateway_status"] == "completed"


def test_execution_dry_run_still_avoids_gateway_invocation() -> None:
    """Dry-run execution never invokes the capability gateway."""
    gateway = FakeRuntimeGateway()
    invoker = CapabilityInvoker(
        policy_adapter=FakePolicyAdapter(),
        runtime_gateway=gateway,  # type: ignore[arg-type]
    )
    run = make_orchestrator(invoker=invoker).execute(
        make_request(plan=make_plan([capability_step()]), mode="dry_run")
    )

    assert run.status == "completed"
    assert gateway.requests == []


def make_orchestrator(invoker: CapabilityInvoker) -> ExecutionOrchestrator:
    """Create an orchestrator."""
    return ExecutionOrchestrator(
        policy_adapter=FakePolicyAdapter(),
        capability_invoker=invoker,
        execution_repository=FakeRepository(),
        telemetry_service=None,
    )


def make_request(*, plan: PlanGraph, mode: str) -> ExecutionRequest:
    """Create an execution request."""
    return ExecutionRequest(
        execution_id="execution-1",
        trace_id="trace-1",
        plan=plan,
        requested_by="actor-1",
        workspace_id="workspace-1",
        mode=mode,  # type: ignore[arg-type]
        approval_present=True,
        metadata={"security_scope": ["workspace:main"]},
    )


def make_plan(steps: list[PlanStep]) -> PlanGraph:
    """Create a plan graph."""
    return PlanGraph(
        plan_id="plan-1",
        intent_id="intent-1",
        goal="generic goal",
        steps=steps,
        dependencies=[],
        risk_level="low",
        approval_required=False,
        status="draft",
    )


def capability_step() -> PlanStep:
    """Create a capability step."""
    return PlanStep(
        step_id="invoke_noop",
        action_type="capability.invoke",
        capability_required="aion.internal.noop",
        risk_level="low",
        status="pending",
    )
