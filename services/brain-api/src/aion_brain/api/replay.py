"""Cognitive replay and Brain snapshot API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.dependencies import (
    get_audit_repository,
    get_brain_loop_service,
    get_cached_observability_repository,
    get_cached_visual_repository,
)
from aion_brain.api.events import get_event_repository
from aion_brain.audit.repository import AuditRepository
from aion_brain.config import get_settings
from aion_brain.contracts.replay import (
    BrainSnapshot,
    ReplayRequest,
    ReplayRun,
    SnapshotCreateRequest,
    SnapshotType,
    TraceComparison,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.events.repository import EventRepository
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.observability.local_recorder import LocalObservabilityRecorder
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.replay.comparator import TraceComparator
from aion_brain.replay.repository import ReplayRepository
from aion_brain.replay.service import ReplayService
from aion_brain.replay.snapshot import ReplayPolicyDenied, SnapshotService

router = APIRouter(prefix="/brain", tags=["replay"])


class TraceSnapshotRequest(BaseModel):
    """Request to snapshot available state for one trace."""

    model_config = ConfigDict(extra="forbid")

    snapshot_type: SnapshotType = "full_trace"
    scope: list[str] = Field(default_factory=list)
    created_by: str | None = None


class SnapshotComparisonRequest(BaseModel):
    """Request to compare two persisted Brain snapshots."""

    model_config = ConfigDict(extra="forbid")

    source_snapshot_id: str
    replay_snapshot_id: str
    scope: list[str] = Field(default_factory=list)
    ignored_fields: list[str] = Field(default_factory=list)


@lru_cache
def get_cached_replay_repository(database_url: str) -> ReplayRepository:
    """Return the cached replay and snapshot repository."""
    return ReplayRepository(database_url)


def get_snapshot_service(
    audit_repository: Annotated[AuditRepository, Depends(get_audit_repository)],
    event_repository: Annotated[EventRepository, Depends(get_event_repository)],
) -> SnapshotService:
    """Return the configured snapshot service."""
    settings = get_settings()
    repository = get_cached_replay_repository(settings.database_url)
    return SnapshotService(
        repository,
        OPAAdapter(settings.opa_url),
        telemetry_service=audit_repository,
        trace_repository=audit_repository,
        event_repository=event_repository,
    )


def get_replay_service(
    snapshot_service: Annotated[SnapshotService, Depends(get_snapshot_service)],
    audit_repository: Annotated[AuditRepository, Depends(get_audit_repository)],
    event_repository: Annotated[EventRepository, Depends(get_event_repository)],
    brain_loop: Annotated[BrainLoopService, Depends(get_brain_loop_service)],
) -> ReplayService:
    """Return the configured local deterministic replay service."""
    settings = get_settings()
    repository = get_cached_replay_repository(settings.database_url)
    return ReplayService(
        repository,
        snapshot_service,
        audit_repository,
        event_repository,
        brain_loop,
        TraceComparator(),
        OPAAdapter(settings.opa_url),
        telemetry_service=audit_repository,
        observability_service=LocalObservabilityRecorder(
            get_cached_observability_repository(settings.database_url),
            get_cached_visual_repository(settings.database_url),
        ),
    )


@router.post("/snapshots", response_model=BrainSnapshot)
def create_snapshot(
    request: SnapshotCreateRequest,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BrainSnapshot:
    """Create a policy-gated content-addressed snapshot."""
    try:
        scoped = service.with_actor_context(actor_context)
        return scoped.create_snapshot(
            request.model_copy(update={"created_by": request.created_by or actor_context.actor_id})
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/snapshots/from-trace/{trace_id}", response_model=BrainSnapshot)
def create_trace_snapshot(
    trace_id: str,
    request: TraceSnapshotRequest,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BrainSnapshot:
    """Snapshot all available canonical artifacts for a trace."""
    try:
        return service.with_actor_context(actor_context).create_trace_snapshot(
            trace_id,
            request.snapshot_type,
            _scope(request.scope, actor_context),
            request.created_by or actor_context.actor_id,
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/snapshots/{snapshot_id}", response_model=BrainSnapshot)
def get_snapshot(
    snapshot_id: str,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BrainSnapshot:
    """Return a policy-authorized snapshot."""
    try:
        snapshot = service.with_actor_context(actor_context).get_snapshot(
            snapshot_id, _scope(scope, actor_context)
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="snapshot_not_found")
    return snapshot


@router.get("/snapshots", response_model=list[BrainSnapshot])
def list_snapshots(
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    trace_id: str | None = None,
    snapshot_type: str | None = None,
    scope: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[BrainSnapshot]:
    """List policy-authorized snapshots."""
    try:
        return service.with_actor_context(actor_context).list_snapshots(
            trace_id, snapshot_type, _scope(scope, actor_context), limit
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/replay", response_model=ReplayRun)
def replay_trace(
    request: ReplayRequest,
    service: Annotated[ReplayService, Depends(get_replay_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReplayRun:
    """Replay a completed trace locally and deterministically."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    return service.with_actor_context(actor_context).replay(enriched)


@router.get("/replay/{replay_id}", response_model=ReplayRun)
def get_replay(
    replay_id: str,
    service: Annotated[ReplayService, Depends(get_replay_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReplayRun:
    """Return a policy-authorized replay run."""
    try:
        replay = service.with_actor_context(actor_context).get_replay(
            replay_id, _scope(scope, actor_context)
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if replay is None:
        raise HTTPException(status_code=404, detail="replay_not_found")
    return replay


@router.post("/replay/compare", response_model=TraceComparison)
def compare_snapshots(
    request: SnapshotComparisonRequest,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> TraceComparison:
    """Compare two policy-authorized snapshots deterministically."""
    scoped = service.with_actor_context(actor_context)
    scope = _scope(request.scope, actor_context)
    try:
        source = scoped.get_snapshot(request.source_snapshot_id, scope)
        replay = scoped.get_snapshot(request.replay_snapshot_id, scope)
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if source is None or replay is None:
        raise HTTPException(status_code=404, detail="snapshot_not_found")
    return TraceComparator().compare(source, replay, request.ignored_fields or None)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value


def _policy_denied(exc: ReplayPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"reason": exc.decision.reason, "constraints": exc.decision.constraints},
    )
