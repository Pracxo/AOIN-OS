"""Local workflow engine tests."""

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.workflows import WorkflowCreateRequest, WorkflowRunRequest, WorkflowStep
from aion_brain.workflows.local_engine import LocalWorkflowEngine
from aion_brain.workflows.repository import WorkflowRepository


class FakePolicyAdapter:
    """Policy fake for workflow tests."""

    def __init__(self, *, deny_actions: set[str] | None = None) -> None:
        self.deny_actions = deny_actions or set()
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allowed = request.action_type not in self.deny_actions
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=allowed,
            approval_required=False,
            reason="allowed" if allowed else "denied",
            constraints=[],
            audit_level="standard",
        )


def test_local_workflow_engine_create_and_dry_run_complete() -> None:
    """Local engine persists and runs a generic workflow in dry-run mode."""
    engine = make_engine()
    workflow = engine.create_workflow(make_create_request(activate=True))

    run = engine.run_workflow(
        WorkflowRunRequest(
            workflow_id=workflow.workflow_id,
            trace_id="trace-1",
            actor_id="actor-1",
            workspace_id="workspace-1",
            mode="dry_run",
        )
    )

    assert run.status == "completed"
    assert run.output["completed_steps"] == 1
    assert run.step_runs[0].status == "completed"


def test_local_workflow_engine_policy_deny_blocks_run() -> None:
    """Policy denial returns a persisted blocked run."""
    repository = WorkflowRepository("sqlite+pysqlite:///:memory:")
    engine = make_engine(repository=repository)
    workflow = engine.create_workflow(make_create_request(activate=True))
    denied_engine = make_engine(
        repository=repository,
        policy_adapter=FakePolicyAdapter(deny_actions={"workflow.run"}),
    )

    run = denied_engine.run_workflow(WorkflowRunRequest(workflow_id=workflow.workflow_id))

    assert run.status == "blocked_by_policy"
    assert run.error["reason"] == "denied"
    assert repository.get_run(run.workflow_run_id) is not None


def test_high_risk_workflow_waits_for_approval() -> None:
    """High-risk workflows require explicit approval before running."""
    engine = make_engine()
    workflow = engine.create_workflow(make_create_request(activate=True, risk_level="high"))

    run = engine.run_workflow(WorkflowRunRequest(workflow_id=workflow.workflow_id))

    assert run.status == "waiting_for_approval"
    assert run.error["reason"] == "approval_required"


def test_retry_transition_persists_next_retry() -> None:
    """Retry transitions persist the next retry timestamp."""
    engine = make_engine()
    workflow = engine.create_workflow(make_create_request(activate=True))
    run = engine.run_workflow(WorkflowRunRequest(workflow_id=workflow.workflow_id))
    failed = run.model_copy(update={"status": "failed"})
    engine._repository.save_run(failed)  # noqa: SLF001

    retry = engine.retry_run(failed.workflow_run_id, "actor-1", "retry")

    assert retry.status == "retry_scheduled"
    assert retry.next_retry_at is not None


def make_engine(
    *,
    repository: WorkflowRepository | None = None,
    policy_adapter: FakePolicyAdapter | None = None,
) -> LocalWorkflowEngine:
    """Create a local engine backed by sqlite."""
    return LocalWorkflowEngine(
        repository=repository or WorkflowRepository("sqlite+pysqlite:///:memory:"),
        policy_adapter=policy_adapter or FakePolicyAdapter(),
    )


def make_create_request(
    *,
    activate: bool = False,
    risk_level: str = "low",
) -> WorkflowCreateRequest:
    """Create a generic workflow create request."""
    return WorkflowCreateRequest(
        workflow_id="workflow-1",
        name="Generic workflow",
        description="Generic workflow description",
        owner_scope=["workspace:main"],
        trigger_type="manual",
        steps=[
            WorkflowStep(
                step_id="noop",
                action_type="noop",
                description="No-op step",
                risk_level="low",
            )
        ],
        risk_level=risk_level,  # type: ignore[arg-type]
        activate=activate,
    )
