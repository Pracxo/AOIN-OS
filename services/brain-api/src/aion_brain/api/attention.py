"""Attention, focus, interrupt, and context budget API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.attention.context_budget import ContextBudgeter
from aion_brain.attention.controller import AttentionController
from aion_brain.attention.focus import FocusService
from aion_brain.attention.interrupts import InterruptRouter
from aion_brain.attention.repository import AttentionRepository
from aion_brain.config import get_settings
from aion_brain.contracts.attention import (
    AttentionDecision,
    AttentionDecisionRequest,
    AttentionSignal,
    AttentionSignalCreateRequest,
    ContextBudget,
    ContextBudgetRequest,
    FocusSession,
    FocusSessionCreateRequest,
    FocusTransitionRequest,
    InterruptCreateRequest,
    InterruptDecisionRequest,
    InterruptRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService

router = APIRouter(prefix="/brain", tags=["attention"])


class ScopeBody(BaseModel):
    """Simple scoped request body."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    limit: int = Field(default=100, ge=1, le=1000)


def get_attention_repository() -> AttentionRepository:
    """Return configured attention repository."""
    return get_cached_attention_repository(get_settings().database_url)


@lru_cache
def get_cached_attention_repository(database_url: str) -> AttentionRepository:
    """Return cached attention repository."""
    return AttentionRepository(database_url)


def get_focus_service(request: Request) -> FocusService:
    """Return focus service from kernel or local dependencies."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "focus_service", None)
    if isinstance(service, FocusService):
        return service
    settings = get_settings()
    return get_cached_focus_service(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_focus_service(database_url: str, opa_url: str) -> FocusService:
    """Return cached focus service."""
    return FocusService(
        get_cached_attention_repository(database_url),
        OPAAdapter(opa_url),
    )


def get_attention_controller(request: Request) -> AttentionController:
    """Return attention controller from kernel or local dependencies."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "attention_controller", None)
    if isinstance(service, AttentionController):
        return service
    settings = get_settings()
    return get_cached_attention_controller(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_attention_controller(
    database_url: str,
    opa_url: str,
) -> AttentionController:
    """Return cached attention controller."""
    policy = OPAAdapter(opa_url)
    settings = get_settings()
    repository = get_cached_attention_repository(database_url)
    working_memory = WorkingMemoryService(
        WorkingMemoryRepository(database_url),
        policy,
        settings=settings,
    )
    focus = FocusService(repository, policy)
    return AttentionController(
        repository,
        policy,
        working_memory_service=working_memory,
        focus_service=focus,
        settings=settings,
    )


def get_interrupt_router(request: Request) -> InterruptRouter:
    """Return interrupt router from kernel or local dependencies."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "interrupt_router", None)
    if isinstance(service, InterruptRouter):
        return service
    settings = get_settings()
    return get_cached_interrupt_router(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_interrupt_router(database_url: str, opa_url: str) -> InterruptRouter:
    """Return cached interrupt router."""
    return InterruptRouter(get_cached_attention_repository(database_url), OPAAdapter(opa_url))


def get_context_budgeter(request: Request) -> ContextBudgeter:
    """Return context budgeter from kernel or local dependencies."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "context_budgeter", None)
    if isinstance(service, ContextBudgeter):
        return service
    settings = get_settings()
    return get_cached_context_budgeter(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_context_budgeter(database_url: str, opa_url: str) -> ContextBudgeter:
    """Return cached context budgeter."""
    return ContextBudgeter(get_cached_attention_repository(database_url), OPAAdapter(opa_url))


@router.post("/attention/signals", response_model=AttentionSignal)
def create_attention_signal(
    request: AttentionSignalCreateRequest,
    controller: Annotated[AttentionController, Depends(get_attention_controller)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AttentionSignal:
    """Create one attention signal."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return controller.create_signal(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/attention/signals", response_model=list[AttentionSignal])
def list_attention_signals(
    controller: Annotated[AttentionController, Depends(get_attention_controller)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    handled: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[AttentionSignal]:
    """List attention signals."""
    try:
        return controller.list_signals(scope or actor_context.security_scope, handled, limit)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/attention/decide", response_model=AttentionDecision)
def decide_attention(
    request: AttentionDecisionRequest,
    controller: Annotated[AttentionController, Depends(get_attention_controller)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AttentionDecision:
    """Return a deterministic attention decision."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "scope": request.scope or actor_context.security_scope,
        }
    )
    try:
        return controller.decide(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/attention/signals/{attention_signal_id}/handled", response_model=AttentionSignal)
def mark_attention_signal_handled(
    attention_signal_id: str,
    controller: Annotated[AttentionController, Depends(get_attention_controller)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> AttentionSignal:
    """Mark one attention signal handled."""
    try:
        return controller.mark_signal_handled(
            attention_signal_id,
            scope or actor_context.security_scope,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/focus", response_model=FocusSession)
def create_focus(
    request: FocusSessionCreateRequest,
    service: Annotated[FocusService, Depends(get_focus_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FocusSession:
    """Create an active focus session."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return service.create_focus_session(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/focus/active", response_model=FocusSession | None)
def get_active_focus(
    service: Annotated[FocusService, Depends(get_focus_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    actor_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
) -> FocusSession | None:
    """Return active focus for actor/workspace."""
    try:
        return service.get_active_focus(
            actor_id or actor_context.actor_id,
            workspace_id or actor_context.workspace_id,
            scope or actor_context.security_scope,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/focus/{focus_session_id}", response_model=FocusSession)
def get_focus(
    focus_session_id: str,
    service: Annotated[FocusService, Depends(get_focus_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> FocusSession:
    """Return one focus session."""
    try:
        session = service.get_focus_session(focus_session_id, scope or actor_context.security_scope)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if session is None:
        raise HTTPException(status_code=404, detail="focus_session_not_found")
    return session


@router.get("/focus", response_model=list[FocusSession])
def list_focus(
    service: Annotated[FocusService, Depends(get_focus_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[FocusSession]:
    """List focus sessions."""
    try:
        return service.list_focus_sessions(scope or actor_context.security_scope, status, limit)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/focus/{focus_session_id}/transition", response_model=FocusSession)
def transition_focus(
    focus_session_id: str,
    request: FocusTransitionRequest,
    service: Annotated[FocusService, Depends(get_focus_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FocusSession:
    """Transition focus status."""
    enriched = request.model_copy(
        update={
            "focus_session_id": focus_session_id,
            "actor_id": request.actor_id or actor_context.actor_id,
        }
    )
    try:
        return service.transition_focus(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/interrupts", response_model=InterruptRecord)
def create_interrupt(
    request: InterruptCreateRequest,
    service: Annotated[InterruptRouter, Depends(get_interrupt_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> InterruptRecord:
    """Create a pending interrupt."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return service.create_interrupt(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/interrupts", response_model=list[InterruptRecord])
def list_interrupts(
    service: Annotated[InterruptRouter, Depends(get_interrupt_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[InterruptRecord]:
    """List interrupts."""
    try:
        return service.list_interrupts(scope or actor_context.security_scope, status, limit)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/interrupts/{interrupt_id}/decide", response_model=InterruptRecord)
def decide_interrupt(
    interrupt_id: str,
    request: InterruptDecisionRequest,
    service: Annotated[InterruptRouter, Depends(get_interrupt_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> InterruptRecord:
    """Decide one interrupt."""
    actor_id = request.actor_id or actor_context.actor_id
    enriched = request.model_copy(
        update={"interrupt_id": interrupt_id, "actor_id": actor_id}
    )
    try:
        return service.decide_interrupt(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/context-budget/allocate", response_model=ContextBudget)
def allocate_context_budget(
    request: ContextBudgetRequest,
    service: Annotated[ContextBudgeter, Depends(get_context_budgeter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ContextBudget:
    """Allocate deterministic context budget."""
    enriched = request.model_copy(update={"scope": request.scope or actor_context.security_scope})
    try:
        return service.allocate(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
