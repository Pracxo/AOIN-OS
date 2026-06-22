"""Run supervision API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.compensation import CompensationPlan, CompensationPlanCreateRequest
from aion_brain.contracts.run_control import RunControlRequest, RunControlRequestCreateRequest
from aion_brain.contracts.run_supervision import (
    RunStatusSample,
    RunSupervisionCreateRequest,
    RunSupervisionRecord,
    RunSupervisionReport,
    RunSupervisionReportRequest,
    RunTimeoutPolicy,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/run-supervision", tags=["run-supervision"])


class ScopeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None


class SampleManyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    status: str | None = "active"
    limit: int = Field(default=100, ge=1, le=1000)


class ReasonBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class HandoffControlBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_present: bool = False


class ProposeCompensationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trigger_reason: str = Field(min_length=1)
    created_by: str | None = None


class ApproveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    approval_present: bool = False
    reason: str = Field(min_length=1)


@router.post("/runs", response_model=RunSupervisionRecord)
def create_run_supervision(
    body: RunSupervisionCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunSupervisionRecord:
    try:
        return container.run_supervision_service.with_actor_context(actor_context).create(
            _run_create_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/runs/{run_supervision_id}", response_model=RunSupervisionRecord)
def get_run_supervision(
    run_supervision_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RunSupervisionRecord:
    try:
        record = container.run_supervision_service.with_actor_context(actor_context).get(
            run_supervision_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="run_supervision_not_found")
    return record


@router.get("/runs", response_model=list[RunSupervisionRecord])
def list_run_supervisions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    target_system: str | None = None,
    status: str | None = None,
    stalled: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RunSupervisionRecord]:
    try:
        return container.run_supervision_query_service.with_actor_context(actor_context).query(
            scope=_scope(scope, actor_context),
            target_system=target_system,
            status=status,
            stalled=stalled,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/runs/{run_supervision_id}/sample", response_model=RunStatusSample)
def sample_run_supervision(
    run_supervision_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    body: Annotated[ScopeBody | None, Body()] = None,
) -> RunStatusSample:
    try:
        scope = body.scope if body is not None else None
        return container.run_status_sampler.with_actor_context(actor_context).sample(
            run_supervision_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sample-many", response_model=list[RunStatusSample])
def sample_many(
    body: SampleManyBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[RunStatusSample]:
    try:
        return container.run_status_sampler.with_actor_context(actor_context).sample_many(
            _scope(body.scope, actor_context), body.status, body.limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/runs/{run_supervision_id}/archive", response_model=RunSupervisionRecord)
def archive_run_supervision(
    run_supervision_id: str,
    body: ReasonBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunSupervisionRecord:
    try:
        return container.run_supervision_service.with_actor_context(actor_context).archive(
            run_supervision_id, actor_id=body.actor_id, reason=body.reason
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/control-requests", response_model=RunControlRequest)
def create_control_request(
    body: RunControlRequestCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunControlRequest:
    try:
        return container.run_control_service.with_actor_context(actor_context).request_control(
            _control_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/control-requests", response_model=list[RunControlRequest])
def list_control_requests(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    run_supervision_id: str | None = None,
    status: str | None = None,
    control_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[RunControlRequest]:
    return container.run_control_service.list_requests(
        run_supervision_id=run_supervision_id,
        status=status,
        control_type=control_type,
        limit=limit,
    )


@router.post("/control-requests/{run_control_request_id}/handoff", response_model=RunControlRequest)
def handoff_control_request(
    run_control_request_id: str,
    body: HandoffControlBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunControlRequest:
    try:
        return container.run_control_service.with_actor_context(actor_context).handoff_control(
            run_control_request_id,
            approval_present=body.approval_present,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/timeout-policies", response_model=RunTimeoutPolicy)
def create_timeout_policy(
    body: RunTimeoutPolicy,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunTimeoutPolicy:
    try:
        return container.timeout_policy_service.with_actor_context(actor_context).create_policy(
            body
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/timeout-policies", response_model=list[RunTimeoutPolicy])
def list_timeout_policies(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    target_system: str | None = None,
    run_type: str | None = None,
) -> list[RunTimeoutPolicy]:
    try:
        return container.timeout_policy_service.with_actor_context(actor_context).list_policies(
            _scope(scope, actor_context),
            status=status,
            target_system=target_system,
            run_type=run_type,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/compensation-plans", response_model=CompensationPlan)
def create_compensation_plan(
    body: CompensationPlanCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompensationPlan:
    try:
        return container.compensation_planner.with_actor_context(actor_context).create_plan(
            _compensation_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/runs/{run_supervision_id}/propose-compensation", response_model=CompensationPlan)
def propose_compensation(
    run_supervision_id: str,
    body: ProposeCompensationBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompensationPlan:
    try:
        return container.compensation_planner.with_actor_context(actor_context).propose_for_run(
            run_supervision_id,
            body.trigger_reason,
            created_by=body.created_by,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/compensation-plans/{compensation_plan_id}", response_model=CompensationPlan)
def get_compensation_plan(
    compensation_plan_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CompensationPlan:
    try:
        plan = container.compensation_planner.with_actor_context(actor_context).get_plan(
            compensation_plan_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if plan is None:
        raise HTTPException(status_code=404, detail="compensation_plan_not_found")
    return plan


@router.get("/compensation-plans", response_model=list[CompensationPlan])
def list_compensation_plans(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    run_supervision_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[CompensationPlan]:
    try:
        return container.compensation_planner.with_actor_context(actor_context).list_plans(
            _scope(scope, actor_context),
            status=status,
            run_supervision_id=run_supervision_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/compensation-plans/{compensation_plan_id}/approve", response_model=CompensationPlan)
def approve_compensation_plan(
    compensation_plan_id: str,
    body: ApproveBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompensationPlan:
    try:
        return container.compensation_planner.with_actor_context(actor_context).approve_plan(
            compensation_plan_id,
            actor_id=body.actor_id,
            approval_present=body.approval_present,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/compensation-plans/{compensation_plan_id}/convert-to-action-proposals",
    response_model=CompensationPlan,
)
def convert_compensation_plan(
    compensation_plan_id: str,
    body: ApproveBody,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompensationPlan:
    try:
        return container.compensation_planner.with_actor_context(
            actor_context
        ).convert_steps_to_action_proposals(
            compensation_plan_id,
            actor_id=body.actor_id,
            approval_present=body.approval_present,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reports", response_model=RunSupervisionReport)
def create_supervision_report(
    body: RunSupervisionReportRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunSupervisionReport:
    try:
        return container.run_supervision_report_service.with_actor_context(actor_context).generate(
            _report_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _run_create_with_context(
    body: RunSupervisionCreateRequest, actor_context: ActorContext
) -> RunSupervisionCreateRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "created_by": body.created_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or _scope(None, actor_context),
        }
    )


def _control_with_context(
    body: RunControlRequestCreateRequest, actor_context: ActorContext
) -> RunControlRequestCreateRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )


def _compensation_with_context(
    body: CompensationPlanCreateRequest, actor_context: ActorContext
) -> CompensationPlanCreateRequest:
    return body.model_copy(update={"created_by": body.created_by or actor_context.actor_id})


def _report_with_context(
    body: RunSupervisionReportRequest, actor_context: ActorContext
) -> RunSupervisionReportRequest:
    return body.model_copy(
        update={
            "created_by": body.created_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or _scope(None, actor_context),
        }
    )


__all__ = ["router"]
