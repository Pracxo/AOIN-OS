"""Idempotency API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.idempotency import IdempotencyRecord
from aion_brain.idempotency.service import IdempotencyService
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/idempotency", tags=["idempotency"])


class ExpireOldRequest(BaseModel):
    """Expire old idempotency records request."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=100, ge=1, le=10000)


class ExpireOldResponse(BaseModel):
    """Expired count response."""

    model_config = ConfigDict(extra="forbid")

    expired: int


def get_idempotency_service(request: Request) -> IdempotencyService:
    """Return configured idempotency service."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.idempotency_service
    raise RuntimeError("idempotency_service_unavailable")


@router.get("/{idempotency_key}", response_model=IdempotencyRecord)
def get_idempotency_record(
    idempotency_key: str,
    service: Annotated[IdempotencyService, Depends(get_idempotency_service)],
) -> IdempotencyRecord:
    """Return one idempotency record."""
    record = service.get(idempotency_key)
    if record is None:
        raise HTTPException(status_code=404, detail="idempotency_record_not_found")
    return record


@router.post("/expire-old", response_model=ExpireOldResponse)
def expire_old(
    body: ExpireOldRequest,
    service: Annotated[IdempotencyService, Depends(get_idempotency_service)],
) -> ExpireOldResponse:
    """Expire old idempotency records."""
    return ExpireOldResponse(expired=service.expire_old(limit=body.limit))
