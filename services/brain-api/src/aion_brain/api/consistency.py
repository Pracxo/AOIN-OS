"""Consistency Guard API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.consistency.checker import ConsistencyChecker
from aion_brain.consistency.leases import ProcessingLeaseService
from aion_brain.contracts.consistency import (
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ProcessingLease,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain", tags=["consistency"])


class LeaseAcquireRequest(BaseModel):
    """Acquire lease body."""

    model_config = ConfigDict(extra="forbid")

    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    ttl_seconds: int | None = Field(default=None, ge=1)


class LeaseReleaseRequest(BaseModel):
    """Release lease body."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)


def get_consistency_checker(request: Request) -> ConsistencyChecker:
    """Return configured consistency checker."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.consistency_checker
    raise RuntimeError("consistency_checker_unavailable")


def get_processing_lease_service(request: Request) -> ProcessingLeaseService:
    """Return configured lease service."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.processing_lease_service
    raise RuntimeError("processing_lease_service_unavailable")


@router.post("/consistency/check", response_model=ConsistencyCheckResult)
def run_consistency_check(
    body: ConsistencyCheckRequest,
    checker: Annotated[ConsistencyChecker, Depends(get_consistency_checker)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConsistencyCheckResult:
    """Run one consistency check."""
    enriched = body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    try:
        return checker.run(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/leases/acquire", response_model=ProcessingLease)
def acquire_lease(
    body: LeaseAcquireRequest,
    service: Annotated[ProcessingLeaseService, Depends(get_processing_lease_service)],
) -> ProcessingLease:
    """Acquire a processing lease."""
    try:
        return service.acquire(
            body.resource_type,
            body.resource_id,
            body.owner_id,
            body.ttl_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/leases/{lease_id}/release", response_model=ProcessingLease)
def release_lease(
    lease_id: str,
    body: LeaseReleaseRequest,
    service: Annotated[ProcessingLeaseService, Depends(get_processing_lease_service)],
) -> ProcessingLease:
    """Release a processing lease."""
    try:
        return service.release(lease_id, body.owner_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
