"""Inbox Deduplication API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.inbox import InboxMessage, InboxReceiveRequest, InboxReceiveResult
from aion_brain.inbox.service import InboxService
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/inbox", tags=["inbox"])


class InboxProcessedRequest(BaseModel):
    """Mark processed body."""

    model_config = ConfigDict(extra="forbid")

    processed_by: str = Field(min_length=1)
    result: dict[str, object] = Field(default_factory=dict)


class InboxFailedRequest(BaseModel):
    """Mark failed body."""

    model_config = ConfigDict(extra="forbid")

    processed_by: str = Field(min_length=1)
    error: dict[str, object] = Field(default_factory=dict)


def get_inbox_service(request: Request) -> InboxService:
    """Return configured inbox service."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.inbox_service
    raise RuntimeError("inbox_service_unavailable")


@router.post("/receive", response_model=InboxReceiveResult)
def receive_inbox_message(
    body: InboxReceiveRequest,
    service: Annotated[InboxService, Depends(get_inbox_service)],
) -> InboxReceiveResult:
    """Record one incoming message."""
    return service.receive(body)


@router.get("", response_model=list[InboxMessage])
def list_inbox_messages(
    service: Annotated[InboxService, Depends(get_inbox_service)],
    status: Annotated[str | None, Query()] = None,
    source: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[InboxMessage]:
    """List inbox messages."""
    return service.list_messages(status=status, source=source, limit=limit)


@router.post("/{inbox_id}/processed", response_model=InboxMessage)
def mark_processed(
    inbox_id: str,
    body: InboxProcessedRequest,
    service: Annotated[InboxService, Depends(get_inbox_service)],
) -> InboxMessage:
    """Mark one inbox message processed."""
    try:
        return service.mark_processed(inbox_id, body.processed_by, body.result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{inbox_id}/failed", response_model=InboxMessage)
def mark_failed(
    inbox_id: str,
    body: InboxFailedRequest,
    service: Annotated[InboxService, Depends(get_inbox_service)],
) -> InboxMessage:
    """Mark one inbox message failed."""
    try:
        return service.mark_failed(inbox_id, body.processed_by, body.error)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
