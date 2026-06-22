"""Visual Brain Projection API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from aion_brain.api.dependencies import get_audit_repository
from aion_brain.audit.repository import AuditRepository
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import (
    BrainMap,
    BrainMapRequest,
    BrainMapSnapshot,
    TraceTimeline,
    TraceTimelineRequest,
    VisualTelemetryQuery,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.visual.map_builder import BrainMapBuilder
from aion_brain.visual.repository import VisualRepository
from aion_brain.visual.service import (
    VisualPolicyDenied,
    VisualProjectionService,
    VisualTelemetryQueryService,
)
from aion_brain.visual.stream import stream_visual_events
from aion_brain.visual.timeline import TraceTimelineBuilder

router = APIRouter(prefix="/brain/visual", tags=["visual"])


def get_visual_repository() -> VisualRepository:
    """Return the configured visual repository."""
    return get_cached_visual_repository(get_settings().database_url)


@lru_cache
def get_cached_visual_repository(database_url: str) -> VisualRepository:
    """Return a cached visual repository."""
    return VisualRepository(database_url)


def get_visual_projection_service() -> VisualProjectionService:
    """Return the configured visual projection service."""
    settings = get_settings()
    repository = get_cached_visual_repository(settings.database_url)
    return VisualProjectionService(
        BrainMapBuilder(repository, settings),
        repository,
        OPAAdapter(settings.opa_url),
    )


def get_visual_query_service() -> VisualTelemetryQueryService:
    """Return the configured telemetry query service."""
    settings = get_settings()
    return VisualTelemetryQueryService(
        get_cached_visual_repository(settings.database_url),
        OPAAdapter(settings.opa_url),
    )


def get_trace_timeline_builder(
    trace_repository: Annotated[AuditRepository, Depends(get_audit_repository)],
) -> TraceTimelineBuilder:
    """Return the configured timeline builder."""
    settings = get_settings()
    return TraceTimelineBuilder(
        trace_repository,
        get_cached_visual_repository(settings.database_url),
        OPAAdapter(settings.opa_url),
    )


@router.post("/map", response_model=BrainMap)
def build_brain_map(
    request: BrainMapRequest,
    service: Annotated[VisualProjectionService, Depends(get_visual_projection_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BrainMap:
    """Build a frontend-agnostic Brain Map."""
    try:
        return service.with_actor_context(actor_context).build_map(request)
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/map/traces/{trace_id}", response_model=BrainMap)
def build_trace_brain_map(
    trace_id: str,
    service: Annotated[VisualProjectionService, Depends(get_visual_projection_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
    scope: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int | None, Query(ge=1, le=5000)] = None,
    include_edges: bool = True,
    include_pulses: bool = True,
    include_clusters: bool = True,
) -> BrainMap:
    """Build a Brain Map for one trace."""
    request = BrainMapRequest(
        trace_id=trace_id,
        workspace_id=actor_context.workspace_id,
        scope=_scope(scope, actor_context),
        limit=limit or settings.visual_default_limit,
        include_edges=include_edges,
        include_pulses=include_pulses,
        include_clusters=include_clusters,
    )
    try:
        return service.with_actor_context(actor_context).build_map(request)
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/snapshots", response_model=BrainMapSnapshot)
def create_snapshot(
    request: BrainMapRequest,
    service: Annotated[VisualProjectionService, Depends(get_visual_projection_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BrainMapSnapshot:
    """Build and persist a Brain Map snapshot."""
    try:
        return service.with_actor_context(actor_context).create_snapshot(request)
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/snapshots/{snapshot_id}", response_model=BrainMapSnapshot)
def get_snapshot(
    snapshot_id: str,
    service: Annotated[VisualProjectionService, Depends(get_visual_projection_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BrainMapSnapshot:
    """Return a persisted Brain Map snapshot."""
    try:
        snapshot = service.with_actor_context(actor_context).get_snapshot(
            snapshot_id,
            _scope(scope, actor_context),
        )
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="visual_snapshot_not_found")
    return snapshot


@router.post("/telemetry/query", response_model=list[VisualTelemetryEvent])
def query_visual_telemetry(
    query: VisualTelemetryQuery,
    service: Annotated[VisualTelemetryQueryService, Depends(get_visual_query_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[VisualTelemetryEvent]:
    """Query canonical visual telemetry."""
    try:
        return service.with_actor_context(actor_context).query(query)
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/telemetry/recent", response_model=list[VisualTelemetryEvent])
def get_recent_visual_telemetry(
    service: Annotated[VisualTelemetryQueryService, Depends(get_visual_query_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[VisualTelemetryEvent]:
    """Return recent canonical visual telemetry."""
    try:
        return service.with_actor_context(actor_context).get_recent(
            _scope(scope, actor_context),
            limit,
        )
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/timeline", response_model=TraceTimeline)
def build_trace_timeline(
    request: TraceTimelineRequest,
    builder: Annotated[TraceTimelineBuilder, Depends(get_trace_timeline_builder)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> TraceTimeline:
    """Build and persist a trace timeline."""
    try:
        return builder.with_actor_context(actor_context).build(request)
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/timeline/{trace_id}", response_model=TraceTimeline)
def get_trace_timeline(
    trace_id: str,
    builder: Annotated[TraceTimelineBuilder, Depends(get_trace_timeline_builder)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> TraceTimeline:
    """Build a current trace timeline."""
    try:
        return builder.with_actor_context(actor_context).build(
            TraceTimelineRequest(trace_id=trace_id, scope=_scope(scope, actor_context))
        )
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/stream")
def stream_visual_telemetry(
    service: Annotated[VisualTelemetryQueryService, Depends(get_visual_query_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    settings: Annotated[Settings, Depends(get_settings)],
    trace_id: str | None = None,
    workspace_id: str | None = None,
    scope: Annotated[list[str] | None, Query()] = None,
    event_types: Annotated[list[str] | None, Query()] = None,
    node_types: Annotated[list[str] | None, Query()] = None,
    max_events: Annotated[int | None, Query(ge=1)] = None,
    poll_interval_seconds: Annotated[float | None, Query(gt=0)] = None,
) -> StreamingResponse:
    """Stream canonical visual telemetry as Server-Sent Events."""
    request_scope = _scope(scope, actor_context)
    scoped_service = service.with_actor_context(actor_context)
    try:
        scoped_service.authorize_stream(trace_id, request_scope)
    except VisualPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    query = VisualTelemetryQuery(
        trace_id=trace_id,
        workspace_id=workspace_id,
        scope=request_scope,
        event_types=event_types or [],
        node_types=node_types or [],
        limit=min(max_events or settings.visual_stream_max_events_default, 1000),
    )
    return StreamingResponse(
        stream_visual_events(
            scoped_service,
            query,
            poll_interval_seconds or settings.visual_stream_poll_interval_seconds,
            max_events or settings.visual_stream_max_events_default,
        ),
        media_type="text/event-stream",
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value


def _policy_denied(exc: VisualPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "reason": exc.decision.reason,
            "decision_id": exc.decision.decision_id,
            "constraints": exc.decision.constraints,
        },
    )
