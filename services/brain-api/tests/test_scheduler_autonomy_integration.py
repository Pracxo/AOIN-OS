"""Scheduler and worker autonomy integration tests."""

from datetime import UTC, datetime

from aion_brain.workflows.local_worker import LocalWorkflowWorker
from aion_brain.workflows.repository import WorkflowRepository
from aion_brain.workflows.scheduler import LocalScheduler
from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_local_workflow_worker_scheduler import (
    FakeEngine,
    FakeScheduleRepository,
    FakeScheduleService,
    FakeWorkflowService,
    make_run,
    make_schedule,
)


def test_scheduler_tick_blocks_when_autonomy_denies() -> None:
    """The scheduler asks autonomy before triggering due workflows."""
    workflow_service = FakeWorkflowService()
    scheduler = LocalScheduler(
        schedule_service=FakeScheduleService(make_schedule()),
        schedule_repository=FakeScheduleRepository(),
        workflow_service=workflow_service,
        enabled=True,
        autonomy_governor=FakeAutonomyGovernor(allow=False),
    )

    result = scheduler.tick(datetime.now(UTC))

    assert result["status"] == "blocked_by_autonomy"
    assert workflow_service.requests == []


def test_worker_start_blocks_when_autonomy_denies() -> None:
    """The local worker does not poll pending work after autonomy denial."""
    repository = WorkflowRepository("sqlite+pysqlite:///:memory:")
    repository.save_run(make_run("run-1"))
    engine = FakeEngine()
    worker = LocalWorkflowWorker(
        repository=repository,
        engine=engine,
        enabled=True,
        max_runs_per_tick=10,
        autonomy_governor=FakeAutonomyGovernor(allow=False),
    )

    result = worker.start_once(max_runs=1)

    assert result["status"] == "blocked_by_autonomy"
    assert engine.ran == []
