"""Dialogue response API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.responses import (
    ResponseComposeRequest,
    ResponseDeliveryRecord,
    ResponseDraft,
    ResponseVerification,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/responses", tags=["responses"])


@router.post("/compose", response_model=ResponseDraft)
def compose_response(
    body: ResponseComposeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResponseDraft:
    """Compose one deterministic response draft."""

    metadata = dict(body.metadata)
    metadata.setdefault("owner_scope", actor_context.security_scope or ["workspace:main"])
    try:
        return container.response_composer.compose(body.model_copy(update={"metadata": metadata}))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/{response_id}", response_model=ResponseDraft)
def get_response(
    response_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ResponseDraft:
    """Return one response draft."""

    response = container.response_composer.get_response(response_id)
    if response is None:
        raise HTTPException(status_code=404, detail="response_not_found")
    return response


@router.post("/{response_id}/verify", response_model=ResponseVerification)
def verify_response(
    response_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ResponseVerification:
    """Verify one response draft locally."""

    try:
        return container.response_verifier.verify(response_id)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{response_id}/deliver-local", response_model=ResponseDeliveryRecord)
def deliver_local_response(
    response_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ResponseDeliveryRecord:
    """Record local API response delivery."""

    try:
        return container.response_delivery_service.deliver_api_return(response_id, None, None)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{response_id}/deliveries", response_model=list[ResponseDeliveryRecord])
def list_response_deliveries(
    response_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> list[ResponseDeliveryRecord]:
    """List local delivery records for one response."""

    return container.response_delivery_service.list_deliveries(response_id=response_id)
