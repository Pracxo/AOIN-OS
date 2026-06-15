"""Working memory API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.config import get_settings
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.working_memory import (
    WorkingMemoryQuery,
    WorkingMemorySlot,
    WorkingMemoryWriteRequest,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService

router = APIRouter(prefix="/brain/working-memory", tags=["working-memory"])


class SweepExpiredRequest(BaseModel):
    """Request to sweep expired working memory slots."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    limit: int = Field(default=100, ge=1, le=1000)


class DeleteSlotResponse(BaseModel):
    """Working memory delete response."""

    model_config = ConfigDict(extra="forbid")

    deleted: bool
    slot_id: str


def get_working_memory_repository() -> WorkingMemoryRepository:
    """Return configured working memory repository."""
    return get_cached_working_memory_repository(get_settings().database_url)


@lru_cache
def get_cached_working_memory_repository(database_url: str) -> WorkingMemoryRepository:
    """Return cached working memory repository."""
    return WorkingMemoryRepository(database_url)


def get_working_memory_service(request: Request) -> WorkingMemoryService:
    """Return working memory service from kernel or local dependencies."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "working_memory_service", None)
    if isinstance(service, WorkingMemoryService):
        return service
    settings = get_settings()
    return get_cached_working_memory_service(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_working_memory_service(database_url: str, opa_url: str) -> WorkingMemoryService:
    """Return cached working memory service."""
    return WorkingMemoryService(
        get_cached_working_memory_repository(database_url),
        OPAAdapter(opa_url),
        settings=get_settings(),
    )


@router.post("", response_model=WorkingMemorySlot)
def write_working_memory_slot(
    request: WorkingMemoryWriteRequest,
    service: Annotated[WorkingMemoryService, Depends(get_working_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkingMemorySlot:
    """Write one working memory slot."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return service.write_slot(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/query", response_model=list[WorkingMemorySlot])
def query_working_memory_slots(
    request: WorkingMemoryQuery,
    service: Annotated[WorkingMemoryService, Depends(get_working_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[WorkingMemorySlot]:
    """Query working memory slots."""
    enriched = request.model_copy(update={"scope": request.scope or actor_context.security_scope})
    try:
        return service.query_slots(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/sweep-expired", response_model=dict[str, object])
def sweep_expired_working_memory(
    request: SweepExpiredRequest,
    service: Annotated[WorkingMemoryService, Depends(get_working_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Soft-delete expired unpinned slots."""
    try:
        return service.sweep_expired(request.scope or actor_context.security_scope, request.limit)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{slot_id}", response_model=WorkingMemorySlot)
def get_working_memory_slot(
    slot_id: str,
    service: Annotated[WorkingMemoryService, Depends(get_working_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> WorkingMemorySlot:
    """Return one working memory slot."""
    try:
        slot = service.get_slot(slot_id, scope or actor_context.security_scope)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if slot is None:
        raise HTTPException(status_code=404, detail="working_memory_slot_not_found")
    return slot


@router.post("/{slot_id}/pin", response_model=WorkingMemorySlot)
def pin_working_memory_slot(
    slot_id: str,
    service: Annotated[WorkingMemoryService, Depends(get_working_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> WorkingMemorySlot:
    """Pin one working memory slot."""
    try:
        return service.pin_slot(slot_id, scope or actor_context.security_scope)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{slot_id}/unpin", response_model=WorkingMemorySlot)
def unpin_working_memory_slot(
    slot_id: str,
    service: Annotated[WorkingMemoryService, Depends(get_working_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> WorkingMemorySlot:
    """Unpin one working memory slot."""
    try:
        return service.unpin_slot(slot_id, scope or actor_context.security_scope)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{slot_id}", response_model=DeleteSlotResponse)
def delete_working_memory_slot(
    slot_id: str,
    service: Annotated[WorkingMemoryService, Depends(get_working_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DeleteSlotResponse:
    """Soft-delete one working memory slot."""
    try:
        deleted = service.delete_slot(slot_id, scope or actor_context.security_scope)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DeleteSlotResponse(deleted=deleted, slot_id=slot_id)
