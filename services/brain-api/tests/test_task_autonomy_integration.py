"""Task runner autonomy integration tests."""

from aion_brain.contracts.tasks import TaskRunRequest
from aion_brain.tasks.runner import CognitiveTaskRunner
from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_task_runner import FakePolicyAdapter, FakeTaskRepository, FakeTaskService, make_task


def test_task_runner_blocks_when_autonomy_denies() -> None:
    """Task runs do not begin when autonomy denies the run."""
    repository = FakeTaskRepository(make_task())
    task_service = FakeTaskService()
    runner = CognitiveTaskRunner(
        task_service=task_service,  # type: ignore[arg-type]
        policy_adapter=FakePolicyAdapter(),
        task_repository=repository,
        autonomy_governor=FakeAutonomyGovernor(allow=False),
    )

    run = runner.run_task(TaskRunRequest(task_id="task-1", run_mode="dry_run"))

    assert run.status == "blocked_by_policy"
    assert run.error["reason"] == "autonomy_denied"
    assert task_service.events[0].event_type == "task_run_blocked"
