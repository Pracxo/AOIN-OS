"""Secret Reference Vault API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.secrets import SecretRef, SecretRefCreateRequest
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.secrets.service import SecretRefService

router = APIRouter(prefix="/brain/secret-refs", tags=["secret-refs"])


class DisableSecretRefRequest(BaseModel):
    """Disable secret ref request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class RotateSecretMetadataRequest(BaseModel):
    """Rotate metadata request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def get_kernel_container(request: Request) -> KernelContainer:
    """Return kernel container."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container


def get_secret_ref_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SecretRefService:
    """Return secret ref service."""
    return container.secret_ref_service


@router.post("", response_model=SecretRef)
def create_secret_ref(
    body: SecretRefCreateRequest,
    service: Annotated[SecretRefService, Depends(get_secret_ref_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SecretRef:
    """Create a metadata-only secret reference."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    try:
        return service.create_secret_ref(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{secret_ref_id}", response_model=SecretRef)
def get_secret_ref(
    secret_ref_id: str,
    service: Annotated[SecretRefService, Depends(get_secret_ref_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SecretRef:
    """Return one secret reference."""
    secret_ref = service.get_secret_ref(secret_ref_id, _scope(scope, actor_context))
    if secret_ref is None:
        raise HTTPException(status_code=404, detail="secret_ref_not_found")
    return secret_ref


@router.get("", response_model=list[SecretRef])
def list_secret_refs(
    service: Annotated[SecretRefService, Depends(get_secret_ref_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
) -> list[SecretRef]:
    """List secret references."""
    return service.list_secret_refs(_scope(scope, actor_context), status=status)


@router.post("/{secret_ref_id}/disable", response_model=SecretRef)
def disable_secret_ref(
    secret_ref_id: str,
    body: DisableSecretRefRequest,
    service: Annotated[SecretRefService, Depends(get_secret_ref_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SecretRef:
    """Disable one secret reference."""
    try:
        return service.disable_secret_ref(
            secret_ref_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{secret_ref_id}/rotate-metadata", response_model=SecretRef)
def rotate_secret_metadata(
    secret_ref_id: str,
    body: RotateSecretMetadataRequest,
    service: Annotated[SecretRefService, Depends(get_secret_ref_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SecretRef:
    """Rotate metadata only."""
    try:
        return service.rotate_metadata(
            secret_ref_id,
            body.actor_id or actor_context.actor_id,
            body.metadata,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]
