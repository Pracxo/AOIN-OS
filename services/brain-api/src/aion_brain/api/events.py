"""Event intake API."""

from functools import lru_cache
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from aion_brain.api.attention import get_attention_controller
from aion_brain.attention.controller import AttentionController
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.attention import AttentionSignalCreateRequest, AttentionSignalType
from aion_brain.contracts.event_reactions import EventDispatchRequest, EventReactionMode
from aion_brain.contracts.events import AIONEvent, EventAcceptance
from aion_brain.contracts.idempotency import IdempotencyCheckRequest
from aion_brain.contracts.outbox import OutboxPublishRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.event_reactions.router import EventReactionRouter
from aion_brain.events.publisher import EventPublisher, NatsEventPublisher
from aion_brain.events.repository import EventRepository
from aion_brain.idempotency.service import IdempotencyService
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.logging import log_event
from aion_brain.outbox.service import OutboxService

router = APIRouter(prefix="/brain", tags=["events"])


def get_event_repository() -> EventRepository:
    """Create the event repository from application settings."""
    return get_cached_event_repository(get_settings().database_url)


def get_event_publisher() -> EventPublisher:
    """Create the event publisher from application settings."""
    return get_cached_event_publisher(get_settings().nats_url)


def get_event_reaction_router_for_intake(request: Request) -> EventReactionRouter | None:
    """Return the kernel event reaction router when available."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "event_reaction_router", None)
    if isinstance(service, EventReactionRouter):
        return service
    return None


def get_idempotency_service_for_intake(request: Request) -> IdempotencyService | None:
    """Return the kernel idempotency service when available."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "idempotency_service", None)
    if isinstance(service, IdempotencyService):
        return service
    return None


def get_outbox_service_for_intake(request: Request) -> OutboxService | None:
    """Return the kernel outbox service when available."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "outbox_service", None)
    if isinstance(service, OutboxService):
        return service
    return None


@lru_cache
def get_cached_event_repository(database_url: str) -> EventRepository:
    """Return a cached event repository for the configured database URL."""
    return EventRepository(database_url)


@lru_cache
def get_cached_event_publisher(nats_url: str) -> EventPublisher:
    """Return a cached event publisher for the configured NATS URL."""
    return NatsEventPublisher(nats_url)


@router.post("/events", response_model=EventAcceptance)
def accept_event(
    event: AIONEvent,
    http_request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[EventRepository, Depends(get_event_repository)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    attention_controller: Annotated[AttentionController, Depends(get_attention_controller)],
    event_router: Annotated[
        EventReactionRouter | None,
        Depends(get_event_reaction_router_for_intake),
    ],
    idempotency_service: Annotated[
        IdempotencyService | None,
        Depends(get_idempotency_service_for_intake),
    ],
    outbox_service: Annotated[OutboxService | None, Depends(get_outbox_service_for_intake)],
) -> EventAcceptance:
    """Accept, persist, and publish a normalized AION event."""
    idempotency_key = _event_idempotency_key(event, http_request)
    idempotency_request = None
    if idempotency_key and settings.idempotency_enabled and idempotency_service is not None:
        idempotency_request = IdempotencyCheckRequest(
            idempotency_key=idempotency_key,
            route="/brain/events",
            actor_id=event.actor_id or actor_context.actor_id,
            workspace_id=event.workspace_id or actor_context.workspace_id,
            request_payload=event.model_dump(mode="json"),
        )
        check = idempotency_service.check(idempotency_request)
        if check.conflict:
            raise HTTPException(status_code=409, detail="idempotency_conflict")
        if check.duplicate and check.record is not None and check.record.response:
            return EventAcceptance.model_validate(check.record.response)
        if check.record is None or check.record.status == "expired":
            idempotency_service.start(idempotency_request)

    accepted_event = normalize_event_ids(event, actor_context)
    persisted_event = repository.save(accepted_event)
    _enqueue_event_publish_outbox(persisted_event, outbox_service, settings)
    published = publisher.publish(persisted_event)

    if not published:
        log_event(
            "event publishing failed",
            settings=settings,
            trace_id=persisted_event.trace_id,
            correlation_id=persisted_event.correlation_id,
            fields={"event_id": persisted_event.event_id, "event_type": persisted_event.event_type},
        )

    _create_attention_signal_for_event(persisted_event, attention_controller)
    _maybe_auto_dispatch_event(persisted_event, settings, actor_context, event_router)

    acceptance = EventAcceptance(
        status="accepted",
        event_id=persisted_event.event_id,
        trace_id=persisted_event.trace_id or "",
        correlation_id=persisted_event.correlation_id or "",
        persisted=True,
        published=published,
    )
    if idempotency_key and idempotency_service is not None:
        idempotency_service.complete(idempotency_key, acceptance.model_dump(mode="json"))
    return acceptance


def _event_idempotency_key(event: AIONEvent, request: Request) -> str | None:
    header = request.headers.get("X-AION-Idempotency-Key")
    if header:
        return header
    value = event.payload.get("idempotency_key")
    if isinstance(value, str) and value:
        return value
    metadata = event.payload.get("metadata")
    if isinstance(metadata, dict):
        nested = metadata.get("idempotency_key")
        if isinstance(nested, str) and nested:
            return nested
    return None


def _enqueue_event_publish_outbox(
    event: AIONEvent,
    outbox_service: OutboxService | None,
    settings: Settings,
) -> None:
    if outbox_service is None or not settings.outbox_enabled:
        return
    try:
        outbox_service.enqueue(
            OutboxPublishRequest(
                message_type="event.publish",
                destination="nats",
                subject=f"aion.events.{event.event_type}",
                payload=event.model_dump(mode="json"),
                headers={"source": "brain.event_intake"},
                trace_id=event.trace_id,
                correlation_id=event.correlation_id,
                max_attempts=settings.outbox_default_max_attempts,
            )
        )
    except Exception:
        return


def _maybe_auto_dispatch_event(
    event: AIONEvent,
    settings: Settings,
    actor_context: ActorContext,
    event_router: EventReactionRouter | None,
) -> None:
    if not settings.event_auto_dispatch_enabled or event_router is None:
        return
    try:
        event_router.dispatch(
            EventDispatchRequest(
                event=event,
                trace_id=event.trace_id or actor_context.trace_id,
                actor_id=event.actor_id or actor_context.actor_id,
                workspace_id=event.workspace_id or actor_context.workspace_id,
                mode=cast(EventReactionMode, settings.event_reaction_default_mode),
                owner_scope=event.security_scope or actor_context.security_scope,
                max_actions=settings.event_reaction_max_actions_default,
                approval_present=False,
                metadata={"auto_dispatch": True},
            )
        )
    except Exception:
        log_event(
            "event auto dispatch failed",
            settings=settings,
            trace_id=event.trace_id,
            correlation_id=event.correlation_id,
            fields={"event_id": event.event_id, "event_type": event.event_type},
        )


def _create_attention_signal_for_event(
    event: AIONEvent,
    controller: AttentionController,
) -> None:
    if event.event_type not in {
        "policy_block",
        "execution_failed",
        "workflow_failed",
        "approval_pending",
        "regression_drift",
        "memory_conflict",
    }:
        return
    signal_type = cast(
        AttentionSignalType,
        "execution_failed" if event.event_type == "workflow_failed" else event.event_type,
    )
    is_high_risk = "failed" in event.event_type or event.event_type == "policy_block"
    try:
        controller.create_signal(
            AttentionSignalCreateRequest(
                attention_signal_id=None,
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                signal_type=signal_type,
                source_type="event",
                source_id=event.event_id,
                title=f"Attention signal for {event.event_type}",
                payload={"event_id": event.event_id, "event_type": event.event_type},
                urgency=0.85 if is_high_risk else 0.75,
                importance=0.80,
                confidence=0.8,
                risk_level="high" if is_high_risk else "medium",
                owner_scope=event.security_scope or ["workspace:main"],
                metadata={"payload_type": event.payload_type},
            )
        )
    except Exception:
        return


def normalize_event_ids(
    event: AIONEvent,
    actor_context: ActorContext | None = None,
) -> AIONEvent:
    """Ensure every accepted event carries trace and correlation IDs."""
    context = actor_context or ActorContext()
    return event.model_copy(
        update={
            "actor_id": event.actor_id or context.actor_id,
            "workspace_id": event.workspace_id or context.workspace_id,
            "security_scope": event.security_scope or context.security_scope,
            "trace_id": event.trace_id or context.trace_id or f"trace-{uuid4().hex}",
            "correlation_id": event.correlation_id
            or context.correlation_id
            or f"corr-{uuid4().hex}",
        }
    )
