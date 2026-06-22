"""Cognitive Task Queue service."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.tasks import (
    CognitiveTask,
    TaskCreateRequest,
    TaskLifecycleEvent,
    TaskTransitionRequest,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.lifecycle.state_machine import require_valid_task_transition
from aion_brain.policy.base import PolicyAdapter
from aion_brain.tasks.publisher import TaskLifecyclePublisher
from aion_brain.tasks.repository import TaskRepository


class TaskService:
    """Policy-gated cognitive task lifecycle service."""

    def __init__(
        self,
        *,
        repository: TaskRepository | object,
        policy_adapter: PolicyAdapter,
        publisher: TaskLifecyclePublisher | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._publisher = publisher
        self._telemetry_service = telemetry_service

    def create_task(self, request: TaskCreateRequest) -> CognitiveTask:
        """Create a proposed cognitive task."""
        decision = self._authorize(
            action_type="task.create",
            resource_id=request.task_id,
            risk_level=request.risk_level,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        task = CognitiveTask(
            task_id=request.task_id or f"task-{uuid4().hex}",
            goal_id=request.goal_id,
            trace_id=request.trace_id,
            plan_id=request.plan_id,
            execution_id=request.execution_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            title=request.title,
            description=request.description,
            task_type=request.task_type,
            status="proposed",
            priority=request.priority,
            risk_level=request.risk_level,
            owner_scope=request.owner_scope,
            input=request.input,
            output={},
            constraints=request.constraints,
            metadata=request.metadata,
            due_at=request.due_at,
            scheduled_for=request.scheduled_for,
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
            cancelled_at=None,
        )
        saved = self._save_task(task)
        self.record_event(
            TaskLifecycleEvent(
                lifecycle_event_id=f"lifecycle-{saved.task_id}-created",
                task_id=saved.task_id,
                goal_id=saved.goal_id,
                trace_id=saved.trace_id,
                event_type="task_created",
                from_status=None,
                to_status=saved.status,
                reason=None,
                payload={"title": saved.title, "task_type": saved.task_type},
                created_at=now,
            )
        )
        self.emit_task(saved, "task_created", 0.5)
        return saved

    def get_task(self, task_id: str, scope: list[str]) -> CognitiveTask | None:
        """Return a task after policy and scope checks."""
        self._authorize_read(task_id, scope)
        task = get_task_from_repository(self._repository, task_id)
        if task is None or not _within_scope(task.owner_scope, scope):
            return None
        return task

    def list_tasks(
        self,
        scope: list[str],
        status: str | None = None,
        goal_id: str | None = None,
        limit: int = 50,
    ) -> list[CognitiveTask]:
        """List tasks after policy checks."""
        self._authorize_read(None, scope)
        list_tasks = getattr(self._repository, "list_tasks", None)
        if callable(list_tasks):
            result = list_tasks(scope=scope, status=status, goal_id=goal_id, limit=limit)
            if isinstance(result, list):
                return [task for task in result if isinstance(task, CognitiveTask)]
        return []

    def transition_task(self, request: TaskTransitionRequest) -> CognitiveTask:
        """Transition a cognitive task lifecycle status."""
        task = get_task_from_repository(self._repository, request.task_id)
        if task is None:
            raise ValueError("task_not_found")
        decision = self._authorize(
            action_type="task.transition",
            resource_id=request.task_id,
            risk_level=task.risk_level,
            trace_id=task.trace_id,
            actor_id=request.actor_id or task.actor_id,
            workspace_id=task.workspace_id,
            scope=task.owner_scope,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        require_valid_task_transition(task.status, request.to_status)
        updated = transition_task_record(task, request.to_status, metadata=request.metadata)
        saved = self._save_task(updated)
        self.record_event(
            TaskLifecycleEvent(
                lifecycle_event_id=f"lifecycle-{saved.task_id}-{uuid4().hex}",
                task_id=saved.task_id,
                goal_id=saved.goal_id,
                trace_id=saved.trace_id,
                event_type="task_transitioned",
                from_status=task.status,
                to_status=saved.status,
                reason=request.reason,
                payload={"actor_id": request.actor_id, "metadata": request.metadata},
                created_at=datetime.now(UTC),
            )
        )
        self.emit_task(saved, "task_transitioned", 0.7)
        return saved

    def record_event(self, event: TaskLifecycleEvent) -> None:
        """Persist and publish a lifecycle event without failing the caller."""
        save_event = getattr(self._repository, "save_lifecycle_event", None)
        if callable(save_event):
            save_event(event)
        if self._publisher is not None:
            self._publisher.publish(event)

    def emit_task(self, task: CognitiveTask, event_type: str, intensity: float) -> None:
        """Emit task visual telemetry when a telemetry service exists."""
        _emit(
            self._telemetry_service,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{task.task_id}-{event_type}",
                trace_id=task.trace_id or task.task_id,
                event_type=event_type,  # type: ignore[arg-type]
                node_type="task",
                node_id=task.task_id,
                edge_from=task.goal_id or task.trace_id,
                edge_to=task.task_id,
                intensity=intensity,
                payload={"status": task.status, "task_type": task.task_type},
                created_at=datetime.now(UTC),
            ),
        )

    def _authorize_read(self, task_id: str | None, scope: list[str]) -> None:
        decision = self._authorize(
            action_type="task.read",
            resource_id=task_id,
            risk_level="low",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            context={},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")

    def _authorize(
        self,
        *,
        action_type: str,
        resource_id: str | None,
        risk_level: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="task",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _save_task(self, task: CognitiveTask) -> CognitiveTask:
        save_task = getattr(self._repository, "save_task", None)
        if callable(save_task):
            result = save_task(task)
            if isinstance(result, CognitiveTask):
                return result
        return task


def get_task_from_repository(repository: object, task_id: str) -> CognitiveTask | None:
    """Return a task from an object implementing get_task."""
    get_task = getattr(repository, "get_task", None)
    if callable(get_task):
        result = get_task(task_id)
        if isinstance(result, CognitiveTask) or result is None:
            return result
    return None


def transition_task_record(
    task: CognitiveTask,
    to_status: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> CognitiveTask:
    """Return a task updated for a lifecycle transition."""
    now = datetime.now(UTC)
    updates: dict[str, Any] = {
        "status": to_status,
        "metadata": {**task.metadata, **(metadata or {})},
        "updated_at": now,
    }
    if to_status == "running":
        updates["started_at"] = now
    if to_status == "completed":
        updates["completed_at"] = now
    if to_status == "cancelled":
        updates["cancelled_at"] = now
    return task.model_copy(update=updates)


def _within_scope(owner_scope: list[str], scope: list[str]) -> bool:
    return not scope or any(item in owner_scope for item in scope)


def _emit(telemetry_service: object | None, event: VisualTelemetryEvent) -> None:
    if telemetry_service is None:
        return
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
