"""Cognitive cycle API."""

from functools import lru_cache
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.config import get_settings
from aion_brain.contracts.cycles import (
    CognitiveCycleRun,
    CognitiveCycleRunRequest,
    CognitiveCycleTemplate,
    CycleStatus,
    CycleType,
    SleepConsolidationRecord,
    SleepConsolidationRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.cycles.maintenance import MaintenanceService
from aion_brain.cycles.orchestrator import CognitiveCycleOrchestrator
from aion_brain.cycles.repository import CognitiveCycleRepository
from aion_brain.cycles.sleep import SleepConsolidationService
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/cycles", tags=["cycles"])


class CycleTemplateDisableRequest(BaseModel):
    """Cycle template disable request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


def get_cycle_orchestrator(request: Request) -> CognitiveCycleOrchestrator:
    """Return the configured cognitive cycle orchestrator."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "cognitive_cycle_orchestrator", None)
    if isinstance(service, CognitiveCycleOrchestrator):
        return service
    settings = get_settings()
    return get_cached_cycle_orchestrator(
        settings.database_url,
        settings.opa_url,
    )


@lru_cache
def get_cached_cycle_repository(database_url: str) -> CognitiveCycleRepository:
    """Return cached cycle repository for fallback apps."""
    return CognitiveCycleRepository(database_url)


@lru_cache
def get_cached_cycle_orchestrator(
    database_url: str,
    opa_url: str,
) -> CognitiveCycleOrchestrator:
    """Build a cached cycle orchestrator outside the kernel container."""
    settings = get_settings()
    repository = get_cached_cycle_repository(database_url)
    maintenance_service = MaintenanceService(settings=settings)
    sleep_service = SleepConsolidationService(
        cycle_repository=repository,
        settings=settings,
    )
    return CognitiveCycleOrchestrator(
        cycle_repository=repository,
        autonomy_governor=None,
        risk_engine=None,
        approval_service=None,
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=None,
        sleep_consolidation_service=sleep_service,
        maintenance_service=maintenance_service,
        settings=settings,
    )


@router.post("/templates", response_model=CognitiveCycleTemplate)
def create_cycle_template(
    template: CognitiveCycleTemplate,
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CognitiveCycleTemplate:
    """Create or update a cognitive cycle template."""
    enriched = template.model_copy(
        update={
            "created_by": template.created_by or actor_context.actor_id,
            "owner_scope": template.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return orchestrator.create_template(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/templates", response_model=list[CognitiveCycleTemplate])
def list_cycle_templates(
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    cycle_type: Annotated[CycleType | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[CognitiveCycleTemplate]:
    """List cognitive cycle templates."""
    try:
        return orchestrator.list_templates(cycle_type=cycle_type, status=status)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/templates/{cycle_template_id}/disable", response_model=CognitiveCycleTemplate)
def disable_cycle_template(
    cycle_template_id: str,
    body: CycleTemplateDisableRequest,
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CognitiveCycleTemplate:
    """Disable a cognitive cycle template."""
    try:
        return orchestrator.disable_template(
            cycle_template_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/run", response_model=CognitiveCycleRun)
def run_cycle(
    request: CognitiveCycleRunRequest,
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CognitiveCycleRun:
    """Run one manual cognitive cycle."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "trace_id": request.trace_id or actor_context.trace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
            "input": {**request.input, "approval_present": request.approval_present},
        }
    )
    try:
        return orchestrator.run_cycle(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = 404 if str(exc).endswith("_not_found") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/sleep-consolidation", response_model=CognitiveCycleRun)
def run_sleep_consolidation(
    request: SleepConsolidationRequest,
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CognitiveCycleRun:
    """Run the manual sleep consolidation cycle."""
    scope = request.scope or actor_context.security_scope
    run_request = CognitiveCycleRunRequest(
        trace_id=actor_context.trace_id,
        actor_id=request.actor_id or actor_context.actor_id,
        workspace_id=request.workspace_id or actor_context.workspace_id,
        cycle_type="sleep_consolidation",
        mode=request.mode,
        owner_scope=scope,
        input={**request.input, "approval_present": request.approval_present},
        approval_present=request.approval_present,
        metadata={"source": "sleep_consolidation_api"},
    )
    try:
        return orchestrator.run_cycle(run_request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/runs/{cycle_run_id}", response_model=CognitiveCycleRun)
def get_cycle_run(
    cycle_run_id: str,
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CognitiveCycleRun:
    """Return one cognitive cycle run."""
    run = orchestrator.get_run(cycle_run_id, scope or actor_context.security_scope)
    if run is None:
        raise HTTPException(status_code=404, detail="cycle_run_not_found")
    return run


@router.get("/runs", response_model=list[CognitiveCycleRun])
def list_cycle_runs(
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    cycle_type: Annotated[CycleType | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[CognitiveCycleRun]:
    """List cognitive cycle runs."""
    return orchestrator.list_runs(
        scope=scope or actor_context.security_scope,
        cycle_type=cycle_type,
        status=status,
        limit=limit,
    )


@router.get("/status/{cycle_type}", response_model=CycleStatus)
def get_cycle_status(
    cycle_type: CycleType,
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CycleStatus:
    """Return status for one cognitive cycle type."""
    return orchestrator.status(cast(str, cycle_type), scope or actor_context.security_scope)


@router.get("/sleep-consolidation/{cycle_run_id}", response_model=SleepConsolidationRecord)
def get_sleep_consolidation_record(
    cycle_run_id: str,
    orchestrator: Annotated[CognitiveCycleOrchestrator, Depends(get_cycle_orchestrator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SleepConsolidationRecord:
    """Return a sleep consolidation record by cycle run."""
    record = orchestrator.get_sleep_record(cycle_run_id, scope or actor_context.security_scope)
    if record is None:
        raise HTTPException(status_code=404, detail="sleep_consolidation_record_not_found")
    return record
