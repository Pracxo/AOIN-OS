"""Cognitive Task Queue API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.dependencies import get_task_repository, get_task_runner, get_task_service
from aion_brain.contracts.tasks import (
    CognitiveTask,
    TaskCreateRequest,
    TaskRunMode,
    TaskRunRecord,
    TaskRunRequest,
    TaskStatus,
    TaskTransitionRequest,
)
from aion_brain.tasks.repository import TaskRepository
from aion_brain.tasks.runner import CognitiveTaskRunner
from aion_brain.tasks.service import TaskService

router = APIRouter(prefix="/brain/tasks", tags=["tasks"])


class TaskTransitionBody(BaseModel):
    """Task transition body without path ID."""

    model_config = ConfigDict(extra="forbid")

    to_status: TaskStatus
    reason: str | None = None
    actor_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class TaskRunBody(BaseModel):
    """Task run body without path ID."""

    model_config = ConfigDict(extra="forbid")

    task_run_id: str | None = None
    trace_id: str | None = None
    run_mode: TaskRunMode = "dry_run"
    approval_present: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


@router.post("", response_model=CognitiveTask)
def create_task(
    request: TaskCreateRequest,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> CognitiveTask:
    """Create a proposed cognitive task."""
    try:
        return service.create_task(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{task_id}", response_model=CognitiveTask)
def get_task(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CognitiveTask:
    """Return a task."""
    task = service.get_task(task_id, scope or ["workspace:main"])
    if task is None:
        raise HTTPException(status_code=404, detail="task_not_found")
    return task


@router.get("", response_model=list[CognitiveTask])
def list_tasks(
    service: Annotated[TaskService, Depends(get_task_service)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    goal_id: str | None = None,
    limit: int = 50,
) -> list[CognitiveTask]:
    """List cognitive tasks."""
    return service.list_tasks(
        scope or ["workspace:main"],
        status=status,
        goal_id=goal_id,
        limit=limit,
    )


@router.post("/{task_id}/transition", response_model=CognitiveTask)
def transition_task(
    task_id: str,
    body: TaskTransitionBody,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> CognitiveTask:
    """Transition a task."""
    try:
        return service.transition_task(
            TaskTransitionRequest(
                task_id=task_id,
                to_status=body.to_status,
                reason=body.reason,
                actor_id=body.actor_id,
                metadata=dict(body.metadata),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{task_id}/run", response_model=TaskRunRecord)
def run_task(
    task_id: str,
    body: TaskRunBody,
    runner: Annotated[CognitiveTaskRunner, Depends(get_task_runner)],
) -> TaskRunRecord:
    """Run a task explicitly."""
    try:
        return runner.run_task(
            TaskRunRequest(
                task_run_id=body.task_run_id,
                task_id=task_id,
                trace_id=body.trace_id,
                run_mode=body.run_mode,
                approval_present=body.approval_present,
                metadata=dict(body.metadata),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{task_id}/runs", response_model=list[TaskRunRecord])
def list_task_runs(
    task_id: str,
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> list[TaskRunRecord]:
    """List task run records."""
    return repository.list_task_runs(task_id)
