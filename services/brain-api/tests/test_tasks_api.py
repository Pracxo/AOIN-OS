"""Cognitive Task Queue API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_task_repository, get_task_runner, get_task_service
from aion_brain.contracts.tasks import (
    CognitiveTask,
    TaskCreateRequest,
    TaskRunRecord,
    TaskRunRequest,
    TaskTransitionRequest,
)
from aion_brain.main import app


class FakeTaskService:
    """Task service fake for API tests."""

    def __init__(self) -> None:
        self.tasks: dict[str, CognitiveTask] = {"task-1": make_task("task-1")}

    def create_task(self, request: TaskCreateRequest) -> CognitiveTask:
        task = make_task(request.task_id or "task-created", title=request.title)
        self.tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str, scope: list[str]) -> CognitiveTask | None:
        task = self.tasks.get(task_id)
        if task and any(item in task.owner_scope for item in scope):
            return task
        return None

    def list_tasks(
        self,
        scope: list[str],
        status: str | None = None,
        goal_id: str | None = None,
        limit: int = 50,
    ) -> list[CognitiveTask]:
        return [
            task
            for task in self.tasks.values()
            if any(item in task.owner_scope for item in scope)
            and (status is None or task.status == status)
            and (goal_id is None or task.goal_id == goal_id)
        ][:limit]

    def transition_task(self, request: TaskTransitionRequest) -> CognitiveTask:
        task = self.tasks[request.task_id].model_copy(update={"status": request.to_status})
        self.tasks[task.task_id] = task
        return task


class FakeTaskRunner:
    """Task runner fake for API tests."""

    def run_task(self, request: TaskRunRequest) -> TaskRunRecord:
        now = datetime.now(UTC)
        return TaskRunRecord(
            task_run_id=request.task_run_id or "task-run-1",
            task_id=request.task_id,
            trace_id=request.trace_id,
            execution_id=None,
            status="completed",
            run_mode=request.run_mode,
            input={},
            output={"dry_run": request.run_mode == "dry_run"},
            error={},
            started_at=now,
            completed_at=now,
            created_at=now,
        )


class FakeTaskRepository:
    """Task repository fake for API tests."""

    def list_task_runs(self, task_id: str) -> list[TaskRunRecord]:
        now = datetime.now(UTC)
        return [
            TaskRunRecord(
                task_run_id="task-run-1",
                task_id=task_id,
                trace_id="trace-1",
                execution_id=None,
                status="completed",
                run_mode="dry_run",
                input={},
                output={"dry_run": True},
                error={},
                started_at=now,
                completed_at=now,
                created_at=now,
            )
        ]


def test_tasks_api_create_get_list_transition_run_and_runs() -> None:
    """Task endpoints expose lifecycle and explicit run controls."""
    service = FakeTaskService()
    app.dependency_overrides[get_task_service] = lambda: service
    app.dependency_overrides[get_task_runner] = lambda: FakeTaskRunner()
    app.dependency_overrides[get_task_repository] = lambda: FakeTaskRepository()
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/tasks",
            json={
                "task_id": "task-created",
                "title": "Task",
                "description": "Task description",
                "task_type": "brain.plan",
                "owner_scope": ["workspace:main"],
            },
        )
        fetched = client.get("/brain/tasks/task-created", params={"scope": "workspace:main"})
        listed = client.get("/brain/tasks", params={"scope": "workspace:main"})
        transitioned = client.post(
            "/brain/tasks/task-created/transition",
            json={"to_status": "queued", "reason": "ready"},
        )
        run = client.post("/brain/tasks/task-created/run", json={"run_mode": "dry_run"})
        runs = client.get("/brain/tasks/task-created/runs")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "queued"
    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert runs.status_code == 200
    assert runs.json()[0]["task_run_id"] == "task-run-1"


def test_tasks_api_rejects_invalid_run_mode() -> None:
    """Invalid task run modes are rejected by API validation."""
    app.dependency_overrides[get_task_runner] = lambda: FakeTaskRunner()
    try:
        response = TestClient(app).post(
            "/brain/tasks/task-1/run",
            json={"run_mode": "background"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def make_task(task_id: str, *, title: str = "Task") -> CognitiveTask:
    """Create a cognitive task."""
    now = datetime.now(UTC)
    return CognitiveTask(
        task_id=task_id,
        goal_id="goal-1",
        trace_id="trace-1",
        title=title,
        description="Task description",
        task_type="brain.plan",
        status="proposed",
        priority="normal",
        risk_level="medium",
        owner_scope=["workspace:main"],
        created_at=now,
        updated_at=now,
    )
