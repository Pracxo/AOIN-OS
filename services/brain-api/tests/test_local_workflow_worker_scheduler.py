"""Local workflow worker and scheduler tests."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.schedules import ScheduleRecord
from aion_brain.contracts.workflows import WorkflowRun, WorkflowRunRequest
from aion_brain.workflows.local_worker import LocalWorkflowWorker
from aion_brain.workflows.repository import WorkflowRepository
from aion_brain.workflows.scheduler import LocalScheduler


class FakePolicyAdapter:
    """Policy fake."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeEngine:
    """Workflow engine fake."""

    def __init__(self) -> None:
        self.ran: list[str] = []

    def run_existing(self, workflow_run_id: str) -> SimpleNamespace:
        self.ran.append(workflow_run_id)
        return SimpleNamespace(workflow_run_id=workflow_run_id)


class FakeWorkflowService:
    """Workflow service fake for scheduler tests."""

    def __init__(self) -> None:
        self.requests: list[WorkflowRunRequest] = []

    def run_workflow(self, request: WorkflowRunRequest) -> SimpleNamespace:
        self.requests.append(request)
        return SimpleNamespace(workflow_run_id="run-1", status="completed")


class FakeScheduleService:
    """Schedule service fake."""

    def __init__(self, schedule: ScheduleRecord) -> None:
        self.schedule = schedule

    def list_schedules(self, status: str | None = None, limit: int = 50) -> list[ScheduleRecord]:
        return [self.schedule] if status in {None, self.schedule.status} else []


class FakeScheduleRepository:
    """Schedule repository fake."""

    def __init__(self) -> None:
        self.saved: list[ScheduleRecord] = []

    def save_schedule(self, schedule: ScheduleRecord) -> ScheduleRecord:
        self.saved.append(schedule)
        return schedule


def test_worker_start_once_is_bounded_and_policy_records_heartbeats() -> None:
    """Worker only runs when explicitly started and respects max_runs."""
    repository = WorkflowRepository("sqlite+pysqlite:///:memory:")
    repository.save_run(make_run("run-1"))
    repository.save_run(make_run("run-2"))
    engine = FakeEngine()
    policy = FakePolicyAdapter()
    worker = LocalWorkflowWorker(
        repository=repository,
        engine=engine,
        enabled=True,
        max_runs_per_tick=10,
        policy_adapter=policy,
    )

    result = worker.start_once(max_runs=1)

    assert result["status"] == "completed"
    assert result["ran"] == 1
    assert engine.ran == ["run-1"]
    assert {request.action_type for request in policy.requests} == {"workflow.heartbeat.write"}


def test_worker_disabled_never_polls() -> None:
    """Disabled worker does not poll or run pending work."""
    worker = LocalWorkflowWorker(
        repository=WorkflowRepository("sqlite+pysqlite:///:memory:"),
        engine=FakeEngine(),
        enabled=False,
        max_runs_per_tick=1,
    )

    assert worker.start_once()["status"] == "skipped"


def test_scheduler_tick_creates_workflow_run_for_due_workflow_schedule() -> None:
    """Scheduler converts due workflow schedules into dry-run workflow requests."""
    workflow_service = FakeWorkflowService()
    repository = FakeScheduleRepository()
    scheduler = LocalScheduler(
        schedule_service=FakeScheduleService(make_schedule()),
        schedule_repository=repository,
        workflow_service=workflow_service,
        enabled=True,
    )

    result = scheduler.tick(datetime.now(UTC))

    assert result["triggered"] == 1
    assert workflow_service.requests[0].workflow_id == "workflow-1"
    assert workflow_service.requests[0].mode == "dry_run"
    assert repository.saved[0].last_run_at is not None


def test_scheduler_disabled_does_not_trigger() -> None:
    """Disabled scheduler returns a skipped result."""
    scheduler = LocalScheduler(
        schedule_service=FakeScheduleService(make_schedule()),
        schedule_repository=FakeScheduleRepository(),
        workflow_service=FakeWorkflowService(),
        enabled=False,
    )

    assert scheduler.tick()["status"] == "skipped"


def make_run(workflow_run_id: str) -> WorkflowRun:
    """Create a pending workflow run."""
    now = datetime.now(UTC)
    return WorkflowRun(
        workflow_run_id=workflow_run_id,
        workflow_id="workflow-1",
        status="pending",
        trigger_type="manual",
        input={},
        output={},
        error={},
        retry_count=0,
        created_at=now,
        updated_at=now,
    )


def make_schedule() -> ScheduleRecord:
    """Create a due workflow schedule."""
    now = datetime.now(UTC)
    return ScheduleRecord(
        schedule_id="schedule-1",
        owner_type="workflow",
        owner_id="workflow-1",
        schedule_type="once",
        schedule_expression="2026-06-12T10:00:00Z",
        timezone="UTC",
        status="active",
        next_run_at=now - timedelta(seconds=1),
        metadata={},
        created_at=now,
        updated_at=now,
    )
