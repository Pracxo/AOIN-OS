"""Event Reaction Router API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.config import get_settings
from aion_brain.contracts.event_reactions import (
    EventDeadLetterRecord,
    EventDispatchRecord,
    EventDispatchRequest,
    EventRouterStatus,
    EventSubscription,
    EventSubscriptionCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.event_reactions.actions import EventReactionActionRunner
from aion_brain.event_reactions.dead_letters import EventDeadLetterService
from aion_brain.event_reactions.matcher import EventTriggerMatcher
from aion_brain.event_reactions.repository import EventReactionRepository
from aion_brain.event_reactions.router import EventReactionRouter
from aion_brain.events.repository import EventRepository
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/event-router", tags=["event-router"])


class DisableSubscriptionRequest(BaseModel):
    """Subscription disable request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class ResolveDeadLetterRequest(BaseModel):
    """Dead-letter resolution request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class ReplayDeadLetterRequest(BaseModel):
    """Dead-letter replay request."""

    model_config = ConfigDict(extra="forbid")

    approval_present: bool = False


def get_event_reaction_router(request: Request) -> EventReactionRouter:
    """Return the configured event reaction router."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "event_reaction_router", None)
    if isinstance(service, EventReactionRouter):
        return service
    settings = get_settings()
    return get_cached_event_reaction_router(
        settings.database_url,
        settings.opa_url,
        settings.event_reaction_router_enabled,
        settings.event_auto_dispatch_enabled,
        settings.event_reaction_default_mode,
        settings.event_reaction_max_actions_default,
        settings.event_dead_letter_enabled,
        settings.event_replay_max_count,
    )


@lru_cache
def get_cached_event_reaction_router(
    database_url: str,
    opa_url: str,
    event_reaction_router_enabled: bool,
    event_auto_dispatch_enabled: bool,
    event_reaction_default_mode: str,
    event_reaction_max_actions_default: int,
    event_dead_letter_enabled: bool,
    event_replay_max_count: int,
) -> EventReactionRouter:
    """Build a cached fallback router outside the kernel container."""
    settings = get_settings().model_copy(
        update={
            "database_url": database_url,
            "opa_url": opa_url,
            "event_reaction_router_enabled": event_reaction_router_enabled,
            "event_auto_dispatch_enabled": event_auto_dispatch_enabled,
            "event_reaction_default_mode": event_reaction_default_mode,
            "event_reaction_max_actions_default": event_reaction_max_actions_default,
            "event_dead_letter_enabled": event_dead_letter_enabled,
            "event_replay_max_count": event_replay_max_count,
        }
    )
    repository = EventReactionRepository(database_url)
    event_repository = EventRepository(database_url)
    policy_adapter = OPAAdapter(opa_url)
    dead_letters = EventDeadLetterService(
        repository=repository,
        event_repository=event_repository,
        policy_adapter=policy_adapter,
        settings=settings,
    )
    router_service = EventReactionRouter(
        repository=repository,
        event_repository=event_repository,
        matcher=EventTriggerMatcher(),
        action_runner=EventReactionActionRunner(),
        dead_letter_service=dead_letters,
        policy_adapter=policy_adapter,
        settings=settings,
    )
    dead_letters.set_router(router_service)
    return router_service


@router.post("/subscriptions", response_model=EventSubscription)
def create_subscription(
    request: EventSubscriptionCreateRequest,
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EventSubscription:
    """Create a reaction subscription."""
    enriched = request.model_copy(
        update={
            "owner_scope": request.owner_scope or actor_context.security_scope,
            "created_by": request.created_by or actor_context.actor_id,
        }
    )
    try:
        return service.create_subscription(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/subscriptions", response_model=list[EventSubscription])
def list_subscriptions(
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[EventSubscription]:
    """List reaction subscriptions."""
    try:
        return service.list_subscriptions(
            scope=scope or actor_context.security_scope,
            status=status,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/subscriptions/{subscription_id}", response_model=EventSubscription)
def get_subscription(
    subscription_id: str,
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EventSubscription:
    """Return one reaction subscription."""
    try:
        subscription = service.get_subscription(
            subscription_id,
            scope or actor_context.security_scope,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if subscription is None:
        raise HTTPException(status_code=404, detail="event_subscription_not_found")
    return subscription


@router.post("/subscriptions/{subscription_id}/disable", response_model=EventSubscription)
def disable_subscription(
    subscription_id: str,
    body: DisableSubscriptionRequest,
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EventSubscription:
    """Disable a reaction subscription."""
    try:
        return service.disable_subscription(
            subscription_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/dispatch", response_model=EventDispatchRecord)
def dispatch_event(
    request: EventDispatchRequest,
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EventDispatchRecord:
    """Manually dispatch an event through the router."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "trace_id": request.trace_id or actor_context.trace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return service.dispatch(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/dispatches/{dispatch_id}", response_model=EventDispatchRecord)
def get_dispatch(
    dispatch_id: str,
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EventDispatchRecord:
    """Return one dispatch."""
    try:
        dispatch = service.get_dispatch(dispatch_id, scope or actor_context.security_scope)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if dispatch is None:
        raise HTTPException(status_code=404, detail="event_dispatch_not_found")
    return dispatch


@router.get("/dispatches", response_model=list[EventDispatchRecord])
def list_dispatches(
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[EventDispatchRecord]:
    """List dispatch records."""
    try:
        return service.list_dispatches(
            scope=scope or actor_context.security_scope,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/dead-letters", response_model=list[EventDeadLetterRecord])
def list_dead_letters(
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[EventDeadLetterRecord]:
    """List event reaction dead letters."""
    try:
        return service.list_dead_letters(
            scope=scope or actor_context.security_scope,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/dead-letters/{dead_letter_id}/resolve", response_model=EventDeadLetterRecord)
def resolve_dead_letter(
    dead_letter_id: str,
    body: ResolveDeadLetterRequest,
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EventDeadLetterRecord:
    """Resolve one event reaction dead letter."""
    try:
        return service.resolve_dead_letter(
            dead_letter_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/dead-letters/{dead_letter_id}/replay", response_model=EventDispatchRecord)
def replay_dead_letter(
    dead_letter_id: str,
    body: ReplayDeadLetterRequest,
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
) -> EventDispatchRecord:
    """Replay one event reaction dead letter."""
    try:
        return service.replay_dead_letter(
            dead_letter_id,
            approval_present=body.approval_present,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status", response_model=EventRouterStatus)
def router_status(
    service: Annotated[EventReactionRouter, Depends(get_event_reaction_router)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EventRouterStatus:
    """Return event reaction router status."""
    return service.status(scope or actor_context.security_scope)
