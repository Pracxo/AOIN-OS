"""Transactional Outbox API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.outbox import (
    OutboxMessage,
    OutboxProcessRequest,
    OutboxProcessResult,
    OutboxPublishRequest,
)
from aion_brain.kernel.container import KernelContainer
from aion_brain.outbox.service import OutboxService

router = APIRouter(prefix="/brain/outbox", tags=["outbox"])


class CancelOutboxRequest(BaseModel):
    """Outbox cancellation body."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None)


def get_outbox_service(request: Request) -> OutboxService:
    """Return configured outbox service."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.outbox_service
    raise RuntimeError("outbox_service_unavailable")


@router.post("", response_model=OutboxMessage)
def enqueue_outbox_message(
    body: OutboxPublishRequest,
    service: Annotated[OutboxService, Depends(get_outbox_service)],
) -> OutboxMessage:
    """Enqueue one outbox message."""
    try:
        return service.enqueue(body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{outbox_id}", response_model=OutboxMessage)
def get_outbox_message(
    outbox_id: str,
    service: Annotated[OutboxService, Depends(get_outbox_service)],
) -> OutboxMessage:
    """Return one outbox message."""
    message = service.get(outbox_id)
    if message is None:
        raise HTTPException(status_code=404, detail="outbox_message_not_found")
    return message


@router.get("", response_model=list[OutboxMessage])
def list_outbox_messages(
    service: Annotated[OutboxService, Depends(get_outbox_service)],
    status: Annotated[str | None, Query()] = None,
    destination: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[OutboxMessage]:
    """List outbox messages."""
    return service.list_messages(status=status, destination=destination, limit=limit)


@router.post("/process-once", response_model=OutboxProcessResult)
def process_once(
    body: OutboxProcessRequest,
    service: Annotated[OutboxService, Depends(get_outbox_service)],
) -> OutboxProcessResult:
    """Manually process outbox messages once."""
    try:
        return service.process_once(body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{outbox_id}/cancel", response_model=OutboxMessage)
def cancel_outbox_message(
    outbox_id: str,
    body: CancelOutboxRequest,
    service: Annotated[OutboxService, Depends(get_outbox_service)],
) -> OutboxMessage:
    """Cancel an outbox message."""
    try:
        return service.cancel(outbox_id, body.reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
