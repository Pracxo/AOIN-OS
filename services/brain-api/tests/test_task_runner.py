"""Cognitive task runner tests."""

from types import SimpleNamespace

from aion_brain.contracts.planning import PlanGraph
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.tasks import (
    CognitiveTask,
    TaskLifecycleEvent,
    TaskRunRecord,
    TaskRunRequest,
)
from aion_brain.tasks.runner import CognitiveTaskRunner


class FakePolicyAdapter:
    """Policy fake for task runner tests."""

    def __init__(self, *, deny: bool = False) -> None:
        self.deny = deny
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=not self.deny,
            approval_required=False,
            reason="allowed" if not self.deny else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeTaskRepository:
    """In-memory task repository fake."""

    def __init__(self, task: CognitiveTask) -> None:
        self.tasks = {task.task_id: task}
        self.runs: list[TaskRunRecord] = []

    def get_task(self, task_id: str) -> CognitiveTask | None:
        return self.tasks.get(task_id)

    def save_task(self, task: CognitiveTask) -> CognitiveTask:
        self.tasks[task.task_id] = task
        return task

    def save_task_run(self, run: TaskRunRecord) -> TaskRunRecord:
        self.runs.append(run)
        return run


class FakeTaskService:
    """Task service fake used by the runner."""

    def __init__(self) -> None:
        self.events: list[TaskLifecycleEvent] = []
        self.emitted: list[str] = []

    def record_event(self, event: TaskLifecycleEvent) -> None:
        self.events.append(event)

    def emit_task(self, task: CognitiveTask, event_type: str, intensity: float) -> None:
        self.emitted.append(f"{task.task_id}:{event_type}:{intensity}")


class FakeExecutionOrchestrator:
    """Execution orchestrator fake for controlled runs."""

    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: object) -> SimpleNamespace:
        self.calls += 1
        return SimpleNamespace(execution_id="execution-1", status="completed")


class FakeWorkflowService:
    """Workflow service fake for explicit task handoff tests."""

    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[object] = []

    def run_workflow(self, request: object) -> SimpleNamespace:
        self.calls += 1
        self.requests.append(request)
        return SimpleNamespace(
            workflow_run_id="workflow-run-1",
            workflow_id="workflow-1",
            status="completed",
            error={},
        )


def test_dry_run_completes_without_execution_orchestrator_call() -> None:
    """Dry-run validates and records the task without execution side effects."""
    task = make_task(task_type="brain.plan")
    repository = FakeTaskRepository(task)
    task_service = FakeTaskService()
    orchestrator = FakeExecutionOrchestrator()
    runner = CognitiveTaskRunner(
        task_service=task_service,  # type: ignore[arg-type]
        policy_adapter=FakePolicyAdapter(),
        task_repository=repository,
        execution_orchestrator=orchestrator,
    )

    run = runner.run_task(TaskRunRequest(task_id="task-1", run_mode="dry_run"))

    assert run.status == "completed"
    assert run.output["dry_run"] is True
    assert orchestrator.calls == 0
    assert repository.tasks["task-1"].status == "completed"
    assert [event.event_type for event in task_service.events] == [
        "task_run_started",
        "task_run_completed",
    ]


def test_task_run_policy_deny_records_blocked_run() -> None:
    """Policy denial creates a blocked run and does not run the task."""
    repository = FakeTaskRepository(make_task())
    task_service = FakeTaskService()
    runner = CognitiveTaskRunner(
        task_service=task_service,  # type: ignore[arg-type]
        policy_adapter=FakePolicyAdapter(deny=True),
        task_repository=repository,
    )

    run = runner.run_task(TaskRunRequest(task_id="task-1", run_mode="dry_run"))

    assert run.status == "blocked_by_policy"
    assert run.error["reason"] == "denied"
    assert repository.tasks["task-1"].status == "proposed"
    assert task_service.events[0].event_type == "task_run_blocked"


def test_high_risk_task_waits_for_approval() -> None:
    """High-risk tasks require explicit approval before running."""
    repository = FakeTaskRepository(make_task(risk_level="high"))
    task_service = FakeTaskService()
    runner = CognitiveTaskRunner(
        task_service=task_service,  # type: ignore[arg-type]
        policy_adapter=FakePolicyAdapter(),
        task_repository=repository,
    )

    run = runner.run_task(TaskRunRequest(task_id="task-1", run_mode="controlled"))

    assert run.status == "waiting_for_approval"
    assert run.error["reason"] == "approval_required"
    assert repository.tasks["task-1"].status == "proposed"


def test_controlled_run_can_delegate_to_execution_orchestrator() -> None:
    """Controlled runs can call the execution orchestrator for stored plans."""
    orchestrator = FakeExecutionOrchestrator()
    task = make_task(
        task_type="brain.plan",
        plan_id="plan-1",
        input_payload={"plan": make_plan().model_dump(mode="json")},
    )
    repository = FakeTaskRepository(task)
    runner = CognitiveTaskRunner(
        task_service=FakeTaskService(),  # type: ignore[arg-type]
        policy_adapter=FakePolicyAdapter(),
        task_repository=repository,
        execution_orchestrator=orchestrator,
    )

    run = runner.run_task(
        TaskRunRequest(task_id="task-1", run_mode="controlled", approval_present=True)
    )

    assert run.status == "completed"
    assert run.output["execution_id"] == "execution-1"
    assert orchestrator.calls == 1


def test_task_runner_creates_workflow_run_only_when_metadata_requests_it() -> None:
    """Explicit metadata can hand a task to the workflow engine in dry-run mode."""
    workflow_service = FakeWorkflowService()
    repository = FakeTaskRepository(make_task())
    runner = CognitiveTaskRunner(
        task_service=FakeTaskService(),  # type: ignore[arg-type]
        policy_adapter=FakePolicyAdapter(),
        task_repository=repository,
        workflow_service=workflow_service,
    )

    run = runner.run_task(
        TaskRunRequest(
            task_id="task-1",
            run_mode="controlled",
            metadata={"run_workflow": True, "workflow_id": "workflow-1"},
        )
    )

    assert run.status == "completed"
    assert run.output["workflow_run_id"] == "workflow-run-1"
    assert run.output["dry_run"] is True
    assert workflow_service.calls == 1


def make_task(
    *,
    task_type: str = "generic",
    risk_level: str = "medium",
    plan_id: str | None = None,
    input_payload: dict[str, object] | None = None,
) -> CognitiveTask:
    """Create a generic cognitive task."""
    return CognitiveTask(
        task_id="task-1",
        goal_id="goal-1",
        trace_id="trace-1",
        plan_id=plan_id,
        title="Task",
        description="Task description",
        task_type=task_type,  # type: ignore[arg-type]
        status="proposed",
        priority="normal",
        risk_level=risk_level,  # type: ignore[arg-type]
        owner_scope=["workspace:main"],
        input=input_payload or {},
    )


def make_plan() -> PlanGraph:
    """Create a generic plan graph."""
    return PlanGraph(
        plan_id="plan-1",
        intent_id="intent-1",
        goal="generic goal",
        steps=[
            {
                "step_id": "create_plan",
                "action_type": "plan.create",
                "capability_required": "plan.create",
                "risk_level": "medium",
                "status": "pending",
            }
        ],
        dependencies=[],
        risk_level="medium",
        approval_required=False,
        status="draft",
        metadata={},
    )
