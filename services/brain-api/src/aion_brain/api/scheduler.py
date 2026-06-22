"""Temporal Scheduler API."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.reminders import ReminderCreateRequest, ReminderRecord
from aion_brain.contracts.scheduler import (
    ScheduleCreateRequest,
    ScheduleDueItem,
    SchedulePolicy,
    ScheduleRecord,
    SchedulerReport,
    SchedulerTickRequest,
    SchedulerTickRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/scheduler", tags=["scheduler"])


class SnoozeRequest(BaseModel):
    """Reminder snooze request."""

    model_config = ConfigDict(extra="forbid")

    snoozed_until: datetime


class ReportRequest(BaseModel):
    """Scheduler report request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    trace_id: str | None = None
    workspace_id: str | None = None


@router.post("/schedules", response_model=ScheduleRecord)
def create_schedule(
    body: ScheduleCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ScheduleRecord:
    try:
        return container.scheduler_schedule_service.with_actor_context(
            actor_context
        ).create_schedule(_schedule_with_context(body, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/schedules", response_model=list[ScheduleRecord])
def list_schedules(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    schedule_type: str | None = None,
    target_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ScheduleRecord]:
    try:
        schedules = container.scheduler_schedule_service.with_actor_context(
            actor_context
        ).list_schedules(
            _scope(scope, actor_context),
            status=status,
            schedule_type=schedule_type,
            limit=limit,
        )
        if target_type is not None:
            schedules = [item for item in schedules if item.target_type == target_type]
        return schedules
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/due-items", response_model=list[ScheduleDueItem])
def list_due_items(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    schedule_id: str | None = None,
    missed: bool | None = None,
    due_before: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ScheduleDueItem]:
    try:
        due_items = container.scheduler_due_item_service.list_due_items(
            _scope(scope, actor_context),
            status=status,
            due_before=due_before,
            schedule_id=schedule_id,
            limit=limit,
        )
        if missed is True:
            due_items = [item for item in due_items if item.status == "missed"]
        if missed is False:
            due_items = [item for item in due_items if item.status != "missed"]
        return due_items
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/reminders", response_model=ReminderRecord)
def create_reminder(
    body: ReminderCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReminderRecord:
    try:
        return container.scheduler_reminder_service.with_actor_context(
            actor_context
        ).create_reminder(_reminder_with_context(body, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/reminders", response_model=list[ReminderRecord])
def list_reminders(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    reminder_type: str | None = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    due_before: datetime | None = None,
    include_deleted: bool = False,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ReminderRecord]:
    try:
        reminders = container.scheduler_reminder_service.with_actor_context(
            actor_context
        ).list_reminders(
            _scope(scope, actor_context),
            status=status,
            due_before=due_before,
            include_deleted=include_deleted,
            limit=limit,
        )
        if reminder_type is not None:
            reminders = [item for item in reminders if item.reminder_type == reminder_type]
        if actor_id is not None:
            reminders = [item for item in reminders if item.actor_id == actor_id]
        if workspace_id is not None:
            reminders = [item for item in reminders if item.workspace_id == workspace_id]
        return reminders
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/tick", response_model=SchedulerTickRun)
def run_scheduler_tick(
    body: SchedulerTickRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SchedulerTickRun:
    try:
        return container.scheduler_tick_orchestrator.run_tick(
            _tick_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/policies", response_model=SchedulePolicy)
def create_schedule_policy(
    body: SchedulePolicy,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SchedulePolicy:
    try:
        return container.schedule_policy_service.create_policy(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/policies", response_model=list[SchedulePolicy])
def list_schedule_policies(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    policy_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[SchedulePolicy]:
    try:
        policies = container.schedule_policy_service.list_policies(
            _scope(scope, actor_context),
            status=status,
            limit=limit,
        )
        if policy_type is not None:
            policies = [item for item in policies if item.policy_type == policy_type]
        return policies
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/report", response_model=SchedulerReport)
def create_scheduler_report(
    body: ReportRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SchedulerReport:
    try:
        return container.scheduler_report_service.create_report(
            _scope(body.scope, actor_context),
            trace_id=body.trace_id or actor_context.trace_id,
            workspace_id=body.workspace_id or actor_context.workspace_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/tick-runs/{tick_run_id}", response_model=SchedulerTickRun)
def get_tick_run(
    tick_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SchedulerTickRun:
    try:
        tick_run = container.scheduler_tick_orchestrator.get_tick_run(
            tick_run_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if tick_run is None:
        raise HTTPException(status_code=404, detail="tick_run_not_found")
    return tick_run


@router.get("/schedules/{schedule_id}", response_model=ScheduleRecord)
def get_schedule(
    schedule_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ScheduleRecord:
    try:
        schedule = container.scheduler_schedule_service.with_actor_context(
            actor_context
        ).get_schedule(schedule_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if schedule is None:
        raise HTTPException(status_code=404, detail="schedule_not_found")
    return schedule


@router.post("/schedules/{schedule_id}/pause", response_model=ScheduleRecord)
def pause_schedule(
    schedule_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ScheduleRecord:
    return _schedule_update(
        container, actor_context, schedule_id, _scope(scope, actor_context), "pause"
    )


@router.post("/schedules/{schedule_id}/resume", response_model=ScheduleRecord)
def resume_schedule(
    schedule_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ScheduleRecord:
    return _schedule_update(
        container, actor_context, schedule_id, _scope(scope, actor_context), "resume"
    )


@router.post("/schedules/{schedule_id}/disable", response_model=ScheduleRecord)
def disable_schedule(
    schedule_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ScheduleRecord:
    return _schedule_update(
        container, actor_context, schedule_id, _scope(scope, actor_context), "disable"
    )


@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    try:
        deleted = container.scheduler_schedule_service.with_actor_context(
            actor_context
        ).delete_schedule(schedule_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": deleted, "schedule_id": schedule_id}


@router.post("/reminders/{reminder_id}/acknowledge", response_model=ReminderRecord)
def acknowledge_reminder(
    reminder_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReminderRecord:
    return _reminder_update(
        container, actor_context, reminder_id, _scope(scope, actor_context), "acknowledge"
    )


@router.post("/reminders/{reminder_id}/snooze", response_model=ReminderRecord)
def snooze_reminder(
    reminder_id: str,
    body: SnoozeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReminderRecord:
    try:
        return container.scheduler_reminder_service.with_actor_context(actor_context).snooze(
            reminder_id,
            _scope(scope, actor_context),
            body.snoozed_until,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reminders/{reminder_id}/dismiss", response_model=ReminderRecord)
def dismiss_reminder(
    reminder_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReminderRecord:
    return _reminder_update(
        container, actor_context, reminder_id, _scope(scope, actor_context), "dismiss"
    )


def _schedule_update(
    container: KernelContainer,
    actor_context: ActorContext,
    schedule_id: str,
    scope: list[str],
    action: str,
) -> ScheduleRecord:
    service = container.scheduler_schedule_service.with_actor_context(actor_context)
    try:
        if action == "pause":
            return service.pause_schedule(schedule_id, scope)
        if action == "resume":
            return service.resume_schedule(schedule_id, scope)
        return service.disable_schedule(schedule_id, scope)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _reminder_update(
    container: KernelContainer,
    actor_context: ActorContext,
    reminder_id: str,
    scope: list[str],
    action: str,
) -> ReminderRecord:
    service = container.scheduler_reminder_service.with_actor_context(actor_context)
    try:
        if action == "acknowledge":
            return service.acknowledge(reminder_id, scope)
        return service.dismiss(reminder_id, scope)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _schedule_with_context(
    body: ScheduleCreateRequest, actor_context: ActorContext
) -> ScheduleCreateRequest:
    return body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
        }
    )


def _reminder_with_context(
    body: ReminderCreateRequest, actor_context: ActorContext
) -> ReminderCreateRequest:
    return body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
        }
    )


def _tick_with_context(
    body: SchedulerTickRequest, actor_context: ActorContext
) -> SchedulerTickRequest:
    return body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "scope": body.scope or actor_context.security_scope,
        }
    )


def _scope(value: list[str] | None, actor_context: ActorContext) -> list[str]:
    return value or actor_context.security_scope or ["workspace:main"]
