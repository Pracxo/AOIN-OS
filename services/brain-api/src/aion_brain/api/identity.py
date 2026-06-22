"""Identity API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from aion_brain.api.dependencies import get_identity_service
from aion_brain.contracts.identity import ActorRecord, PermissionGrant
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.identity.service import IdentityPolicyDenied, IdentityService

router = APIRouter(prefix="/brain", tags=["identity"])


class ReasonBody(BaseModel):
    """Reason-only mutation body."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


@router.get("/me", response_model=ActorContext)
def current_actor_context(
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActorContext:
    """Return the current dev actor context."""
    return actor_context


@router.post("/identity/actors", response_model=ActorRecord)
def create_actor(
    record: ActorRecord,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActorRecord:
    """Create an actor."""
    try:
        return service.with_actor_context(actor_context).create_actor(record)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/identity/actors/{actor_id}", response_model=ActorRecord)
def get_actor(
    actor_id: str,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActorRecord:
    """Return an actor."""
    try:
        actor = service.with_actor_context(actor_context).get_actor(actor_id)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if actor is None:
        raise HTTPException(status_code=404, detail="actor_not_found")
    return actor


@router.get("/identity/actors", response_model=list[ActorRecord])
def list_actors(
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
    limit: int = 50,
) -> list[ActorRecord]:
    """List actors."""
    try:
        return service.with_actor_context(actor_context).list_actors(status=status, limit=limit)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/identity/actors/{actor_id}/disable", response_model=ActorRecord)
def disable_actor(
    actor_id: str,
    body: ReasonBody,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActorRecord:
    """Disable an actor."""
    try:
        return service.with_actor_context(actor_context).disable_actor(actor_id, body.reason)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/identity/permissions", response_model=PermissionGrant)
def create_permission_grant(
    record: PermissionGrant,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PermissionGrant:
    """Create a permission grant."""
    try:
        return service.with_actor_context(actor_context).create_permission_grant(record)
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/identity/permissions", response_model=list[PermissionGrant])
def list_permission_grants(
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    actor_id: str | None = None,
    workspace_id: str | None = None,
    role: str | None = None,
) -> list[PermissionGrant]:
    """List permission grants."""
    try:
        return service.with_actor_context(actor_context).list_permission_grants(
            actor_id=actor_id,
            workspace_id=workspace_id,
            role=role,
        )
    except IdentityPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/identity/permissions/{grant_id}/revoke", response_model=PermissionGrant)
def revoke_permission_grant(
    grant_id: str,
    body: ReasonBody,
    service: Annotated[IdentityService, Depends(get_identity_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PermissionGrant:
    """Revoke a permission grant."""
    try:
        return service.with_actor_context(actor_context).revoke_permission_grant(
            grant_id,
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
