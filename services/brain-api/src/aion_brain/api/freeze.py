"""Freeze gate API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.freeze import FreezeGateRun, FreezeGateRunRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.freeze.gate import FreezeGateService
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/freeze-gate", tags=["freeze-gate"])


def get_freeze_gate_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> FreezeGateService:
    """Return freeze gate service."""
    return container.freeze_gate_service


@router.post("/run", response_model=FreezeGateRun)
def run_freeze_gate(
    body: FreezeGateRunRequest,
    request: Request,
    service: Annotated[FreezeGateService, Depends(get_freeze_gate_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FreezeGateRun:
    """Run the deterministic v0.1 freeze gate."""
    body = body.model_copy(
        update={
            "requested_by": body.requested_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
        }
    )
    return service.run(body, app=request.app)


@router.get("/{freeze_gate_id}", response_model=FreezeGateRun)
def get_freeze_gate(
    freeze_gate_id: str,
    service: Annotated[FreezeGateService, Depends(get_freeze_gate_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> FreezeGateRun:
    """Return one freeze gate run."""
    run = service.get(freeze_gate_id, _scope(scope, actor_context))
    if run is None:
        raise HTTPException(status_code=404, detail="freeze_gate_not_found")
    return run


@router.get("", response_model=list[FreezeGateRun])
def list_freeze_gates(
    service: Annotated[FreezeGateService, Depends(get_freeze_gate_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    version: str | None = None,
    status: str | None = None,
) -> list[FreezeGateRun]:
    """List freeze gate runs."""
    return service.list(_scope(scope, actor_context), version=version, status=status)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
