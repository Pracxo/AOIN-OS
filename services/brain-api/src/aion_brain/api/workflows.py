"""Durable workflow API."""

from functools import lru_cache
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.approvals import get_cached_approval_service
from aion_brain.config import get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.workflows import (
    TemporalAdapterStatus,
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowEngineStatus,
    WorkflowRun,
    WorkflowRunRequest,
    WorkflowTransitionRequest,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.workflows.local_engine import LocalWorkflowEngine
from aion_brain.workflows.local_worker import LocalWorkflowWorker
from aion_brain.workflows.repository import WorkflowRepository
from aion_brain.workflows.scheduler import LocalScheduler
from aion_brain.workflows.service import WorkflowService
from aion_brain.workflows.temporal_adapter import TemporalAdapter
from aion_brain.workflows.temporal_compat import TemporalCompat

router = APIRouter(prefix="/brain/workflows", tags=["workflows"])


class WorkflowStatusBody(BaseModel):
    """Workflow status transition body."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = None
    actor_id: str | None = None


class WorkflowRetryBody(BaseModel):
    """Workflow retry request body."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str | None = None


class SchedulerTickBody(BaseModel):
    """Scheduler tick request."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = True


class WorkerStartBody(BaseModel):
    """Local worker bounded start request."""

    model_config = ConfigDict(extra="forbid")

    max_runs: int | None = Field(default=1, ge=0)


def get_workflow_service(request: Request) -> WorkflowService:
    """Return the configured workflow service."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.workflow_service
    settings = get_settings()
    return get_cached_workflow_service(
        settings.database_url,
        settings.opa_url,
        settings.workflow_engine_adapter,
        settings.workflow_local_worker_enabled,
        settings.temporal_enabled,
        settings.temporal_endpoint_ref,
        settings.temporal_namespace,
        settings.temporal_task_queue,
    )


def get_workflow_scheduler(request: Request) -> LocalScheduler:
    """Return the configured local scheduler."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.workflow_scheduler
    return get_cached_workflow_scheduler()


def get_workflow_worker(request: Request) -> LocalWorkflowWorker:
    """Return the configured local workflow worker."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.workflow_worker
    return get_cached_workflow_worker()


def get_workflow_policy_adapter(request: Request) -> object:
    """Return the configured policy adapter."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.policy_adapter
    return OPAAdapter(get_settings().opa_url)


@lru_cache
def get_cached_workflow_service(
    database_url: str,
    opa_url: str,
    workflow_engine_adapter: str,
    workflow_local_worker_enabled: bool,
    temporal_enabled: bool,
    temporal_endpoint_ref: str,
    temporal_namespace: str,
    temporal_task_queue: str,
) -> WorkflowService:
    """Build a cached workflow service outside the kernel container."""
    settings = get_settings()
    repository = WorkflowRepository(database_url)
    temporal_adapter = TemporalAdapter(
        enabled=temporal_enabled,
        endpoint_ref=temporal_endpoint_ref,
        namespace=temporal_namespace,
        task_queue=temporal_task_queue,
        compat=TemporalCompat(),
    )
    temporal_status = temporal_adapter.temporal_status()
    local_engine = LocalWorkflowEngine(
        repository=repository,
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=None,
        temporal_available=temporal_status.package_available,
        temporal_enabled=temporal_enabled,
        local_worker_enabled=workflow_local_worker_enabled,
        approval_service=get_cached_approval_service(
            database_url,
            opa_url,
            settings.risk_engine_enabled,
            settings.guardrails_enabled,
            settings.approvals_enabled,
            settings.approval_default_expiry_hours,
            settings.high_risk_requires_approval,
            settings.critical_risk_blocks_by_default,
        ),
    )
    return WorkflowService(
        local_engine=local_engine,
        temporal_adapter=temporal_adapter,
        workflow_engine_adapter=workflow_engine_adapter,
        temporal_enabled=temporal_enabled,
    )


@lru_cache
def get_cached_workflow_scheduler() -> LocalScheduler:
    """Build a cached disabled scheduler outside the kernel container."""
    settings = get_settings()
    service = get_cached_workflow_service(
        settings.database_url,
        settings.opa_url,
        settings.workflow_engine_adapter,
        settings.workflow_local_worker_enabled,
        settings.temporal_enabled,
        settings.temporal_endpoint_ref,
        settings.temporal_namespace,
        settings.temporal_task_queue,
    )
    return LocalScheduler(
        schedule_service=object(),
        schedule_repository=object(),
        workflow_service=service,
        enabled=False,
        telemetry_service=None,
    )


@lru_cache
def get_cached_workflow_worker() -> LocalWorkflowWorker:
    """Build a cached disabled worker outside the kernel container."""
    settings = get_settings()
    repository = WorkflowRepository(settings.database_url)
    service = get_cached_workflow_service(
        settings.database_url,
        settings.opa_url,
        settings.workflow_engine_adapter,
        settings.workflow_local_worker_enabled,
        settings.temporal_enabled,
        settings.temporal_endpoint_ref,
        settings.temporal_namespace,
        settings.temporal_task_queue,
    )
    return LocalWorkflowWorker(
        repository=repository,
        engine=service,
        enabled=False,
        max_runs_per_tick=1,
        policy_adapter=OPAAdapter(settings.opa_url),
    )


@router.post("", response_model=WorkflowDefinition)
def create_workflow(
    request: WorkflowCreateRequest,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowDefinition:
    """Create a workflow definition."""
    enriched = request.model_copy(
        update={
            "created_by": request.created_by or actor_context.actor_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return service.create_workflow(enriched)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs/{workflow_run_id}", response_model=WorkflowRun)
def get_workflow_run(
    workflow_run_id: str,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> WorkflowRun:
    """Return one workflow run."""
    run = service.get_run(workflow_run_id, scope or actor_context.security_scope)
    if run is None:
        raise HTTPException(status_code=404, detail="workflow_run_not_found")
    return run


@router.get("/runs", response_model=list[WorkflowRun])
def list_workflow_runs(
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    workflow_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[WorkflowRun]:
    """List workflow runs."""
    return service.list_runs(
        workflow_id=workflow_id,
        status=status,
        scope=scope or actor_context.security_scope,
        limit=limit,
    )


@router.post("/run", response_model=WorkflowRun)
def run_workflow(
    request: WorkflowRunRequest,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowRun:
    """Run a workflow."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
        }
    )
    try:
        return service.run_workflow(enriched)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{workflow_run_id}/pause", response_model=WorkflowRun)
def pause_workflow_run(
    workflow_run_id: str,
    request: WorkflowTransitionRequest,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowRun:
    """Pause a workflow run."""
    return _transition(service.pause_run, workflow_run_id, request, actor_context)


@router.post("/runs/{workflow_run_id}/resume", response_model=WorkflowRun)
def resume_workflow_run(
    workflow_run_id: str,
    request: WorkflowTransitionRequest,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowRun:
    """Resume a workflow run."""
    return _transition(service.resume_run, workflow_run_id, request, actor_context)


@router.post("/runs/{workflow_run_id}/cancel", response_model=WorkflowRun)
def cancel_workflow_run(
    workflow_run_id: str,
    request: WorkflowTransitionRequest,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowRun:
    """Cancel a workflow run."""
    return _transition(service.cancel_run, workflow_run_id, request, actor_context)


@router.post("/runs/{workflow_run_id}/retry", response_model=WorkflowRun)
def retry_workflow_run(
    workflow_run_id: str,
    body: WorkflowRetryBody,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowRun:
    """Retry a workflow run."""
    try:
        return service.retry_run(
            workflow_run_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/scheduler/tick", response_model=dict[str, object])
def scheduler_tick(
    body: SchedulerTickBody,
    scheduler: Annotated[LocalScheduler, Depends(get_workflow_scheduler)],
    policy_adapter: Annotated[object, Depends(get_workflow_policy_adapter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Run one scheduler tick."""
    _authorize_control_action(policy_adapter, actor_context, "workflow.scheduler.tick")
    if body.dry_run:
        return scheduler.tick()
    return scheduler.tick()


@router.post("/worker/start-once", response_model=dict[str, object])
def worker_start_once(
    body: WorkerStartBody,
    worker: Annotated[LocalWorkflowWorker, Depends(get_workflow_worker)],
    policy_adapter: Annotated[object, Depends(get_workflow_policy_adapter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Run one local worker tick."""
    _authorize_control_action(policy_adapter, actor_context, "workflow.worker.start_once")
    return worker.start_once(body.max_runs)


@router.get("/engine/status", response_model=WorkflowEngineStatus)
def workflow_engine_status(
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    policy_adapter: Annotated[object, Depends(get_workflow_policy_adapter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowEngineStatus:
    """Return workflow engine status."""
    _authorize_control_action(policy_adapter, actor_context, "workflow.engine.status")
    return service.engine_status()


@router.get("/temporal/status", response_model=TemporalAdapterStatus)
def temporal_status(
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    policy_adapter: Annotated[object, Depends(get_workflow_policy_adapter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> TemporalAdapterStatus:
    """Return optional Temporal adapter status."""
    _authorize_control_action(policy_adapter, actor_context, "workflow.temporal.status")
    return service.temporal_status()


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
def get_workflow(
    workflow_id: str,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> WorkflowDefinition:
    """Return one workflow definition."""
    workflow = service.get_workflow(workflow_id, scope or actor_context.security_scope)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    return workflow


@router.get("", response_model=list[WorkflowDefinition])
def list_workflows(
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: int = 50,
) -> list[WorkflowDefinition]:
    """List workflow definitions."""
    return service.list_workflows(
        scope=scope or actor_context.security_scope,
        status=status,
        limit=limit,
    )


@router.post("/{workflow_id}/activate", response_model=WorkflowDefinition)
def activate_workflow(
    workflow_id: str,
    body: WorkflowStatusBody,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowDefinition:
    """Activate a workflow definition."""
    return _workflow_status(service, workflow_id, "active", body, actor_context)


@router.post("/{workflow_id}/disable", response_model=WorkflowDefinition)
def disable_workflow(
    workflow_id: str,
    body: WorkflowStatusBody,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkflowDefinition:
    """Disable a workflow definition."""
    return _workflow_status(service, workflow_id, "disabled", body, actor_context)


def _transition(
    transition: object,
    workflow_run_id: str,
    request: WorkflowTransitionRequest,
    actor_context: ActorContext,
) -> WorkflowRun:
    if not callable(transition):
        raise HTTPException(status_code=500, detail="workflow_transition_unavailable")
    try:
        return cast(
            WorkflowRun,
            transition(
                request.model_copy(
                    update={
                        "workflow_run_id": workflow_run_id,
                        "actor_id": request.actor_id or actor_context.actor_id,
                    }
                )
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _workflow_status(
    service: WorkflowService,
    workflow_id: str,
    status: str,
    body: WorkflowStatusBody,
    actor_context: ActorContext,
) -> WorkflowDefinition:
    try:
        return service.update_workflow_status(
            workflow_id,
            status,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _authorize_control_action(
    policy_adapter: object,
    actor_context: ActorContext,
    action_type: str,
) -> None:
    authorize = getattr(policy_adapter, "authorize", None)
    if not callable(authorize):
        raise HTTPException(status_code=500, detail="policy_adapter_unavailable")
    decision = authorize(
        PolicyRequest(
            request_id=f"{action_type}-{actor_context.actor_id}",
            trace_id=None,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            action_type=action_type,
            resource_type="workflow",
            resource_id=None,
            risk_level="medium",
            approval_present=True,
            requested_permissions=[],
            security_scope=actor_context.security_scope,
            context={"actor_context": actor_context.model_dump(mode="json")},
        )
    )
    if not decision.allow:
        raise HTTPException(status_code=403, detail={"reason": decision.reason})
