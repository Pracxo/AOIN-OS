"""Workflow repository tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.workflows import (
    WorkflowDefinition,
    WorkflowHeartbeat,
    WorkflowRun,
    WorkflowStep,
    WorkflowWorkerRecord,
)
from aion_brain.workflows.repository import WorkflowRepository


def test_workflow_repository_persists_definition_run_step_heartbeat_and_worker() -> None:
    """Repository stores the workflow ledger without Docker services."""
    repository = WorkflowRepository("sqlite+pysqlite:///:memory:")
    workflow = repository.save_workflow(make_workflow())
    run = repository.save_run(make_run())
    step_run = run.step_runs[0]
    saved_step = repository.save_step_run(step_run)
    heartbeat = repository.save_heartbeat(
        WorkflowHeartbeat(
            heartbeat_id="heartbeat-1",
            workflow_run_id=run.workflow_run_id,
            worker_id="worker-1",
            status="running",
            payload={},
        )
    )
    worker = repository.save_worker(
        WorkflowWorkerRecord(
            worker_id="worker-1",
            worker_type="local_workflow",
            status="idle",
            capabilities=["workflow.run"],
            metadata={},
        )
    )

    assert repository.get_workflow(workflow.workflow_id) == workflow
    assert repository.get_run(run.workflow_run_id) is not None
    assert saved_step.workflow_run_id == run.workflow_run_id
    assert heartbeat.created_at is not None
    assert worker.status == "idle"


def test_repository_lists_scoped_workflows_and_due_runs() -> None:
    """Repository filters definitions by scope and runs by runnable state."""
    repository = WorkflowRepository("sqlite+pysqlite:///:memory:")
    repository.save_workflow(make_workflow(owner_scope=["workspace:a"]))
    repository.save_workflow(make_workflow(workflow_id="workflow-2", owner_scope=["workspace:b"]))
    repository.save_run(make_run(status="pending"))
    repository.save_run(
        make_run(
            workflow_run_id="run-2",
            status="retry_scheduled",
            next_retry_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )

    workflows = repository.list_workflows(scope=["workspace:a"])
    runnable = repository.list_runnable_runs(limit=10, now=datetime.now(UTC))

    assert [workflow.workflow_id for workflow in workflows] == ["workflow-1"]
    assert {run.workflow_run_id for run in runnable} == {"run-1", "run-2"}


def make_workflow(
    workflow_id: str = "workflow-1",
    *,
    owner_scope: list[str] | None = None,
) -> WorkflowDefinition:
    """Create a generic workflow definition."""
    now = datetime.now(UTC)
    return WorkflowDefinition(
        workflow_id=workflow_id,
        name="Generic workflow",
        description="Generic workflow description",
        status="active",
        owner_scope=owner_scope or ["workspace:main"],
        trigger_type="manual",
        trigger_config={},
        steps=[
            WorkflowStep(
                step_id="noop",
                action_type="noop",
                description="No-op step",
                risk_level="low",
            )
        ],
        risk_level="low",
        created_at=now,
        updated_at=now,
    )


def make_run(
    workflow_run_id: str = "run-1",
    *,
    status: str = "pending",
    next_retry_at: datetime | None = None,
) -> WorkflowRun:
    """Create a workflow run with one step."""
    now = datetime.now(UTC)
    return WorkflowRun(
        workflow_run_id=workflow_run_id,
        workflow_id="workflow-1",
        trace_id="trace-1",
        status=status,  # type: ignore[arg-type]
        trigger_type="manual",
        input={},
        output={},
        error={},
        retry_count=0,
        step_runs=[
            {
                "workflow_step_run_id": "step-run-1",
                "workflow_run_id": workflow_run_id,
                "step_id": "noop",
                "action_type": "noop",
                "status": "pending",
                "attempt": 1,
            }
        ],
        next_retry_at=next_retry_at,
        created_at=now,
        updated_at=now,
    )
