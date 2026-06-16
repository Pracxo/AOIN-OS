"""Situation model API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.situations import (
    ContextContinuityRecord,
    ContextContinuityRequest,
    SituationCloseRequest,
    SituationCreateRequest,
    SituationProjectionRequest,
    SituationProjectionResult,
    SituationQuery,
    SituationQueryResult,
    SituationRecord,
)
from aion_brain.contracts.temporal_state import (
    StateAtom,
    StateAtomCreateRequest,
    StateTransition,
    TemporalStateWindow,
    TemporalStateWindowRequest,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/situations", tags=["situations"])


@router.post("", response_model=SituationRecord)
def create_situation(
    body: SituationCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SituationRecord:
    """Create one situation record."""
    try:
        return container.situation_service.create(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/query", response_model=SituationQueryResult)
def query_situations(
    body: SituationQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SituationQueryResult:
    """Query situations and optional state atoms."""
    try:
        return container.situation_query_service.query(
            body.model_copy(update={"scope": body.scope or actor_context.security_scope})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/{situation_id}/close", response_model=SituationRecord)
def close_situation(
    situation_id: str,
    body: SituationCloseRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SituationRecord:
    """Close one situation."""
    try:
        return container.situation_service.close(
            situation_id,
            _scope(scope, actor_context),
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/state-atoms", response_model=StateAtom)
def create_state_atom(
    body: StateAtomCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> StateAtom:
    """Create one state atom."""
    try:
        return container.state_atom_service.create(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/state-atoms/{state_atom_id}", response_model=StateAtom)
def get_state_atom(
    state_atom_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> StateAtom:
    """Return one state atom."""
    try:
        atom = container.state_atom_service.get(state_atom_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if atom is None:
        raise HTTPException(status_code=404, detail="state_atom_not_found")
    return atom


@router.get("/state-atoms", response_model=list[StateAtom])
def list_state_atoms(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    situation_id: str | None = None,
    trace_id: str | None = None,
    status: Annotated[list[str] | None, Query()] = None,
    source_type: str | None = None,
    source_id: str | None = None,
    include_deleted: bool = False,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[StateAtom]:
    """List visible state atoms."""
    try:
        return container.state_atom_service.list_atoms(
            scope=_scope(scope, actor_context),
            situation_id=situation_id,
            trace_id=trace_id,
            statuses=status,
            source_type=source_type,
            source_id=source_id,
            include_deleted=include_deleted,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/project", response_model=SituationProjectionResult)
def project_situations(
    body: SituationProjectionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SituationProjectionResult:
    """Run deterministic situation projection."""
    return container.situation_projector.project(
        body.model_copy(
            update={
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "trace_id": body.trace_id or actor_context.trace_id,
                "actor_id": body.actor_id or actor_context.actor_id,
                "workspace_id": body.workspace_id or actor_context.workspace_id,
            }
        )
    )


@router.get("/projection-runs/{projection_run_id}", response_model=SituationProjectionResult)
def get_projection_run(
    projection_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SituationProjectionResult:
    """Return one persisted projection run."""
    run = container.situation_projector.get_projection_run(projection_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="projection_run_not_found")
    return run


@router.get("/transitions", response_model=list[StateTransition])
def list_transitions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    trace_id: str | None = None,
    situation_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[StateTransition]:
    """List state transitions."""
    return container.situation_repository.list_transitions(
        trace_id=trace_id,
        situation_id=situation_id,
        status=status,
        limit=limit,
    )


@router.post("/temporal-windows", response_model=TemporalStateWindow)
def create_temporal_window(
    body: TemporalStateWindowRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> TemporalStateWindow:
    """Create one temporal state window."""
    try:
        return container.temporal_state_window_service.create(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/temporal-windows/{temporal_window_id}", response_model=TemporalStateWindow)
def get_temporal_window(
    temporal_window_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> TemporalStateWindow:
    """Return one temporal state window."""
    try:
        window = container.temporal_state_window_service.get(
            temporal_window_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if window is None:
        raise HTTPException(status_code=404, detail="temporal_window_not_found")
    return window


@router.get("/temporal-windows", response_model=list[TemporalStateWindow])
def list_temporal_windows(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    trace_id: str | None = None,
    window_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[TemporalStateWindow]:
    """List temporal state windows."""
    try:
        return container.temporal_state_window_service.list_windows(
            scope=_scope(scope, actor_context),
            trace_id=trace_id,
            window_type=window_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/continuity", response_model=ContextContinuityRecord)
def record_continuity(
    body: ContextContinuityRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ContextContinuityRecord:
    """Record context continuity."""
    try:
        return container.context_continuity_service.record(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/continuity", response_model=list[ContextContinuityRecord])
def list_continuity(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    trace_id: str | None = None,
    dialogue_session_id: str | None = None,
    focus_session_id: str | None = None,
    situation_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ContextContinuityRecord]:
    """List context continuity records."""
    try:
        return container.context_continuity_service.list_records(
            scope=_scope(scope, actor_context),
            trace_id=trace_id,
            dialogue_session_id=dialogue_session_id,
            focus_session_id=focus_session_id,
            situation_id=situation_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/{situation_id}", response_model=SituationRecord)
def get_situation(
    situation_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SituationRecord:
    """Return one situation."""
    try:
        situation = container.situation_service.get(situation_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if situation is None:
        raise HTTPException(status_code=404, detail="situation_not_found")
    return situation


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope
