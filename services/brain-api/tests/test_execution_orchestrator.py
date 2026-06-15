"""ExecutionOrchestrator tests."""

from aion_brain.contracts.execution import (
    ApprovalCheckpoint,
    CapabilityInvocationRecord,
    ExecutionRequest,
    ExecutionRun,
    ExecutionStepRun,
)
from aion_brain.contracts.planning import PlanGraph, PlanStep
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.execution.orchestrator import ExecutionOrchestrator


class FakePolicyAdapter:
    """Policy fake for orchestrator tests."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=request.risk_level in {"high", "critical"}
            and not request.approval_present,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["blocked"],
            audit_level="standard" if allow else "high",
        )


class FakeCapabilityInvoker:
    """Capability invoker fake."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def invoke(
        self,
        capability_id: str,
        payload: dict[str, object],
        execution_id: str | None,
        step_run_id: str | None,
        trace_id: str | None,
    ) -> CapabilityInvocationRecord:
        self.calls.append(capability_id)
        return CapabilityInvocationRecord(
            invocation_id=f"invocation-{capability_id}",
            execution_id=execution_id,
            step_run_id=step_run_id,
            trace_id=trace_id,
            capability_id=capability_id,
            input=payload,
            output={"invoked": False},
            status="not_implemented",
            policy_decision_id="decision-capability",
            latency_ms=0,
            created_at=make_datetime(),
        )


class FakeRepository:
    """Execution repository fake."""

    def __init__(self) -> None:
        self.executions: list[ExecutionRun] = []
        self.steps: list[ExecutionStepRun] = []
        self.approvals: list[ApprovalCheckpoint] = []
        self.invocations: list[CapabilityInvocationRecord] = []

    def save_execution(self, run: ExecutionRun) -> ExecutionRun:
        self.executions.append(run)
        return run

    def save_step(self, step: ExecutionStepRun) -> ExecutionStepRun:
        self.steps.append(step)
        return step

    def save_approval(self, approval: ApprovalCheckpoint) -> ApprovalCheckpoint:
        self.approvals.append(approval)
        return approval

    def save_capability_invocation(
        self,
        record: CapabilityInvocationRecord,
    ) -> CapabilityInvocationRecord:
        self.invocations.append(record)
        return record


class FakeTelemetry:
    """Telemetry fake."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_dry_run_does_not_invoke_capability() -> None:
    """Dry run validates capability steps but does not invoke."""
    invoker = FakeCapabilityInvoker()
    run = make_orchestrator(invoker=invoker).execute(
        make_request(plan=make_plan([capability_step()]))
    )

    assert run.status == "completed"
    assert run.steps[0].output["dry_run"] is True
    assert invoker.calls == []


def test_controlled_mode_calls_capability_invoker() -> None:
    """Controlled capability steps go through CapabilityInvoker."""
    invoker = FakeCapabilityInvoker()
    run = make_orchestrator(invoker=invoker).execute(
        make_request(plan=make_plan([capability_step()]), mode="controlled")
    )

    assert run.status == "completed"
    assert invoker.calls == ["test.echo"]
    assert run.capability_invocations[0].status == "not_implemented"


def test_high_risk_step_creates_approval_checkpoint() -> None:
    """High-risk steps wait for approval when approval is missing."""
    run = make_orchestrator().execute(make_request(plan=make_plan([high_risk_step()])))

    assert run.status == "waiting_for_approval"
    assert run.approvals[0].status == "pending"


def test_policy_deny_blocks_execution() -> None:
    """Policy denial blocks the execution run."""
    run = make_orchestrator(policy=FakePolicyAdapter(deny_action="execution.step")).execute(
        make_request()
    )

    assert run.status == "blocked_by_policy"
    assert run.steps[0].status == "blocked_by_policy"


def make_orchestrator(
    *,
    policy: FakePolicyAdapter | None = None,
    invoker: FakeCapabilityInvoker | None = None,
) -> ExecutionOrchestrator:
    """Create an orchestrator with fakes."""
    return ExecutionOrchestrator(
        policy_adapter=policy or FakePolicyAdapter(),
        capability_invoker=invoker or FakeCapabilityInvoker(),  # type: ignore[arg-type]
        execution_repository=FakeRepository(),
        telemetry_service=FakeTelemetry(),
    )


def make_request(
    *,
    plan: PlanGraph | None = None,
    mode: str = "dry_run",
) -> ExecutionRequest:
    """Create an execution request."""
    return ExecutionRequest(
        execution_id="execution-1",
        trace_id="trace-1",
        plan=plan or make_plan([safe_step()]),
        requested_by="actor-1",
        workspace_id="workspace-1",
        mode=mode,
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
        risk_level=max((step.risk_level for step in steps), key=_risk_rank),
        approval_required=any(step.risk_level in {"high", "critical"} for step in steps),
        status="draft",
    )


def safe_step() -> PlanStep:
    """Create a safe internal step."""
    return PlanStep(
        step_id="retrieve_context",
        action_type="memory.retrieve",
        capability_required="memory.retrieve",
        risk_level="low",
        status="pending",
    )


def capability_step() -> PlanStep:
    """Create a capability invocation step."""
    return PlanStep(
        step_id="invoke_test_echo",
        action_type="capability.invoke",
        capability_required="test.echo",
        risk_level="low",
        status="pending",
    )


def high_risk_step() -> PlanStep:
    """Create a high-risk generic step."""
    return PlanStep(
        step_id="wait_for_execution_layer",
        action_type="plan.create",
        capability_required="plan.create",
        risk_level="high",
        status="pending",
    )


def _risk_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(value, 0)


def make_datetime() -> object:
    """Return current datetime without another top-level import in the fake."""
    from datetime import UTC, datetime

    return datetime.now(UTC)
