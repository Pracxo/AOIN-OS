"""Cognitive Task Queue service tests."""

import pytest

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.tasks import (
    CognitiveTask,
    TaskCreateRequest,
    TaskLifecycleEvent,
    TaskTransitionRequest,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.tasks.publisher import NoopTaskLifecyclePublisher
from aion_brain.tasks.service import TaskService


class FakePolicyAdapter:
    """Policy fake for task service tests."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeTaskRepository:
    """In-memory task repository fake."""

    def __init__(self) -> None:
        self.tasks: dict[str, CognitiveTask] = {}
        self.events: list[TaskLifecycleEvent] = []

    def save_task(self, task: CognitiveTask) -> CognitiveTask:
        self.tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> CognitiveTask | None:
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        goal_id: str | None = None,
        limit: int = 50,
    ) -> list[CognitiveTask]:
        tasks = [
            task
            for task in self.tasks.values()
            if (not scope or any(item in task.owner_scope for item in scope))
            and (status is None or task.status == status)
            and (goal_id is None or task.goal_id == goal_id)
        ]
        return tasks[:limit]

    def save_lifecycle_event(self, event: TaskLifecycleEvent) -> TaskLifecycleEvent:
        self.events.append(event)
        return event


class FakeTelemetry:
    """Telemetry fake for task service tests."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_task_service_creates_task_records_events_and_telemetry() -> None:
    """Creating a task persists the task and lifecycle event."""
    repository = FakeTaskRepository()
    policy = FakePolicyAdapter()
    publisher = NoopTaskLifecyclePublisher(published=False)
    telemetry = FakeTelemetry()
    service = TaskService(
        repository=repository,
        policy_adapter=policy,
        publisher=publisher,
        telemetry_service=telemetry,
    )

    task = service.create_task(
        TaskCreateRequest(
            task_id="task-1",
            goal_id="goal-1",
            trace_id="trace-1",
            title="Hold a generic task",
            description="Track the lifecycle of a generic task.",
            task_type="brain.plan",
            owner_scope=["workspace:main"],
        )
    )

    assert task.status == "proposed"
    assert repository.tasks["task-1"] == task
    assert repository.events[0].event_type == "task_created"
    assert publisher.events[0].task_id == "task-1"
    assert telemetry.events[0].event_type == "task_created"
    assert policy.requests[0].action_type == "task.create"


def test_task_service_transitions_task_through_state_machine() -> None:
    """Transitioning a task records lifecycle movement."""
    repository = FakeTaskRepository()
    service = TaskService(
        repository=repository,
        policy_adapter=FakePolicyAdapter(),
        publisher=NoopTaskLifecyclePublisher(),
    )
    service.create_task(
        TaskCreateRequest(
            task_id="task-1",
            title="Task",
            description="Task description",
            owner_scope=["workspace:main"],
        )
    )

    updated = service.transition_task(
        TaskTransitionRequest(
            task_id="task-1",
            to_status="queued",
            reason="ready",
            actor_id="actor-1",
            metadata={"queue": "default"},
        )
    )

    assert updated.status == "queued"
    assert updated.metadata["queue"] == "default"
    assert repository.events[-1].event_type == "task_transitioned"
    assert repository.events[-1].from_status == "proposed"
    assert repository.events[-1].to_status == "queued"


def test_task_service_policy_deny_blocks_create() -> None:
    """Policy denial blocks task creation before persistence."""
    repository = FakeTaskRepository()
    service = TaskService(
        repository=repository,
        policy_adapter=FakePolicyAdapter(deny_action="task.create"),
    )

    with pytest.raises(ValueError, match="policy_denied"):
        service.create_task(
            TaskCreateRequest(
                task_id="task-1",
                title="Task",
                description="Task description",
                owner_scope=["workspace:main"],
            )
        )

    assert repository.tasks == {}
