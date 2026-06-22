"""Operator Control Tower API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.operator import (
    OperatorAcknowledgement,
    OperatorAcknowledgementRequest,
    OperatorActionItem,
    OperatorOverview,
    OperatorOverviewRequest,
    OperatorQueueSummary,
    OperatorReadinessReport,
    OperatorRunbookLink,
    OperatorSnapshot,
    OperatorSnapshotRequest,
    OperatorStatusCard,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.control_tower import OperatorControlTowerService
from aion_brain.operator.runbooks import RunbookRegistry
from aion_brain.operator.snapshots import OperatorSnapshotService

router = APIRouter(prefix="/brain/operator", tags=["operator"])


def get_operator_control_tower(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> OperatorControlTowerService:
    return container.operator_control_tower_service


def get_operator_action_center(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ActionCenterService:
    return container.operator_action_center_service


def get_operator_snapshot_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> OperatorSnapshotService:
    return container.operator_snapshot_service


def get_runbook_registry(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> RunbookRegistry:
    return container.operator_runbook_registry


@router.post("/overview", response_model=OperatorOverview)
def operator_overview(
    body: OperatorOverviewRequest,
    service: Annotated[OperatorControlTowerService, Depends(get_operator_control_tower)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorOverview:
    """Return one aggregated local operator overview."""
    try:
        return service.overview(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                }
            ),
            actor_context=actor_context,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/status-cards", response_model=list[OperatorStatusCard])
def operator_status_cards(
    service: Annotated[OperatorControlTowerService, Depends(get_operator_control_tower)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[OperatorStatusCard]:
    """Return local operator status cards."""
    try:
        return service.status_cards(_scope(scope, actor_context), actor_context=actor_context)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/queues", response_model=list[OperatorQueueSummary])
def operator_queues(
    service: Annotated[OperatorControlTowerService, Depends(get_operator_control_tower)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[OperatorQueueSummary]:
    """Return local queue summaries."""
    try:
        return service.queues(_scope(scope, actor_context), actor_context=actor_context)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/actions", response_model=list[OperatorActionItem])
def operator_actions(
    service: Annotated[OperatorControlTowerService, Depends(get_operator_control_tower)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[OperatorActionItem]:
    """Return local action-center recommendations."""
    try:
        return service.actions(_scope(scope, actor_context), limit, actor_context=actor_context)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/actions/acknowledge", response_model=OperatorAcknowledgement)
def acknowledge_operator_action(
    body: OperatorAcknowledgementRequest,
    service: Annotated[ActionCenterService, Depends(get_operator_action_center)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorAcknowledgement:
    """Record acknowledgement without resolving the source issue."""
    try:
        return service.acknowledge(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/acknowledgements", response_model=list[OperatorAcknowledgement])
def operator_acknowledgements(
    service: Annotated[ActionCenterService, Depends(get_operator_action_center)],
    source_type: str | None = None,
    source_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[OperatorAcknowledgement]:
    """List local operator acknowledgements."""
    try:
        return service.list_acknowledgements(source_type, source_id, limit)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/readiness", response_model=OperatorReadinessReport)
def operator_readiness(
    service: Annotated[OperatorControlTowerService, Depends(get_operator_control_tower)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> OperatorReadinessReport:
    """Return local operator readiness."""
    try:
        return service.readiness(_scope(scope, actor_context), actor_context=actor_context)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/snapshots", response_model=OperatorSnapshot)
def create_operator_snapshot(
    body: OperatorSnapshotRequest,
    service: Annotated[OperatorSnapshotService, Depends(get_operator_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorSnapshot:
    """Create a local operator snapshot."""
    try:
        return service.create_snapshot(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "generated_by": body.generated_by or actor_context.actor_id,
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/snapshots/{operator_snapshot_id}", response_model=OperatorSnapshot)
def get_operator_snapshot(
    operator_snapshot_id: str,
    service: Annotated[OperatorSnapshotService, Depends(get_operator_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> OperatorSnapshot:
    """Return one local operator snapshot."""
    try:
        snapshot = service.get_snapshot(operator_snapshot_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="operator_snapshot_not_found")
    return snapshot


@router.get("/snapshots", response_model=list[OperatorSnapshot])
def list_operator_snapshots(
    service: Annotated[OperatorSnapshotService, Depends(get_operator_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    snapshot_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[OperatorSnapshot]:
    """List local operator snapshots."""
    try:
        return service.list_snapshots(
            _scope(scope, actor_context),
            snapshot_type=snapshot_type,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/runbooks", response_model=list[OperatorRunbookLink])
def operator_runbooks(
    registry: Annotated[RunbookRegistry, Depends(get_runbook_registry)],
    category: str | None = None,
) -> list[OperatorRunbookLink]:
    """Return local runbook links."""
    if category:
        return registry.get_by_category(category)
    return registry.list_runbooks()


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]
