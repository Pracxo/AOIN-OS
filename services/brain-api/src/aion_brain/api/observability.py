"""Local Observability Spine API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.visual import get_cached_visual_repository, get_trace_timeline_builder
from aion_brain.config import get_settings
from aion_brain.contracts.observability import ObservabilityEvent, ObservabilitySummary
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.visual import TraceTimeline, TraceTimelineRequest
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.observability.local_recorder import LocalObservabilityRecorder
from aion_brain.observability.repository import ObservabilityRepository
from aion_brain.observability.service import ObservabilityService
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.visual.service import VisualPolicyDenied
from aion_brain.visual.timeline import TraceTimelineBuilder

router = APIRouter(prefix="/brain/observability", tags=["observability"])


@lru_cache
def get_cached_observability_repository(database_url: str) -> ObservabilityRepository:
    """Return a cached observability repository."""
    return ObservabilityRepository(database_url)


def get_observability_service() -> ObservabilityService:
    """Return the configured local observability service."""
    settings = get_settings()
    return ObservabilityService(
        LocalObservabilityRecorder(
            get_cached_observability_repository(settings.database_url),
            get_cached_visual_repository(settings.database_url),
        ),
        OPAAdapter(settings.opa_url),
    )


@router.post("/events", response_model=ObservabilityEvent)
def record_observability_event(
    event: ObservabilityEvent,
    service: Annotated[ObservabilityService, Depends(get_observability_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ObservabilityEvent:
    """Record a sanitized local observability event."""
    try:
        return service.with_actor_context(actor_context).record_event(event)
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/summary", response_model=ObservabilitySummary)
def get_observability_summary(
    service: Annotated[ObservabilityService, Depends(get_observability_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ObservabilitySummary:
    """Return a local observability summary."""
    try:
        return service.with_actor_context(actor_context).summarize(
            scope or actor_context.security_scope
        )
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/traces/{trace_id}/timeline", response_model=TraceTimeline)
def get_observability_trace_timeline(
    trace_id: str,
    builder: Annotated[TraceTimelineBuilder, Depends(get_trace_timeline_builder)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> TraceTimeline:
    """Return the trace timeline through the observability alias."""
    try:
        return builder.with_actor_context(actor_context).build(
            TraceTimelineRequest(
                trace_id=trace_id,
                scope=scope or actor_context.security_scope,
            )
        )
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


def _policy_denied(exc: VisualPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"reason": exc.decision.reason, "constraints": exc.decision.constraints},
    )
