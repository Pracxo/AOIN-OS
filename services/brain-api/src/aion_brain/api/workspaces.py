"""Workspace API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from aion_brain.api.dependencies import get_identity_service
from aion_brain.contracts.identity import WorkspaceMembership, WorkspaceRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.identity.service import IdentityPolicyDenied, IdentityService

router = APIRouter(prefix="/brain/workspaces", tags=["workspaces"])


class ReasonBody(BaseModel):
    """Reason-only mutation body."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


@router.post("", response_model=WorkspaceRecord)
def create_workspace(
    record: WorkspaceRecord,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkspaceRecord:
    """Create a workspace."""
    try:
        return service.with_actor_context(actor_context).create_workspace(record)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/{workspace_id}", response_model=WorkspaceRecord)
def get_workspace(
    workspace_id: str,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkspaceRecord:
    """Return a workspace."""
    try:
        workspace = service.with_actor_context(actor_context).get_workspace(workspace_id)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if workspace is None:
        raise HTTPException(status_code=404, detail="workspace_not_found")
    return workspace


@router.get("", response_model=list[WorkspaceRecord])
def list_workspaces(
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
    limit: int = 50,
) -> list[WorkspaceRecord]:
    """List workspaces."""
    try:
        return service.with_actor_context(actor_context).list_workspaces(
            status=status,
            limit=limit,
        )
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/{workspace_id}/archive", response_model=WorkspaceRecord)
def archive_workspace(
    workspace_id: str,
    body: ReasonBody,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkspaceRecord:
    """Archive a workspace."""
    try:
        return service.with_actor_context(actor_context).archive_workspace(
            workspace_id,
            body.reason,
        )
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{workspace_id}/memberships", response_model=WorkspaceMembership)
def add_membership(
    workspace_id: str,
    record: WorkspaceMembership,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkspaceMembership:
    """Add a workspace membership."""
    try:
        membership = record.model_copy(update={"workspace_id": workspace_id})
        return service.with_actor_context(actor_context).add_membership(membership)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/{workspace_id}/memberships", response_model=list[WorkspaceMembership])
def list_memberships(
    workspace_id: str,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[WorkspaceMembership]:
    """List workspace memberships."""
    try:
        return service.with_actor_context(actor_context).list_memberships(workspace_id=workspace_id)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post(
    "/{workspace_id}/memberships/{membership_id}/revoke",
    response_model=WorkspaceMembership,
)
def revoke_membership(
    workspace_id: str,
    membership_id: str,
    body: ReasonBody,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WorkspaceMembership:
    """Revoke a workspace membership."""
    try:
        return service.with_actor_context(actor_context).revoke_membership(
            membership_id,
            body.reason,
        )
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _policy_denied(exc: IdentityPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "reason": exc.decision.reason,
            "decision_id": exc.decision.decision_id,
            "constraints": exc.decision.constraints,
        },
    )
