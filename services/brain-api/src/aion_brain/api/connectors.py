"""Connector Registry API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.connectors.service import ConnectorService
from aion_brain.contracts.connectors import ConnectorCreateRequest, ConnectorDefinition
from aion_brain.contracts.sandbox import SandboxValidationResult
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/connectors", tags=["connectors"])


class DisableConnectorRequest(BaseModel):
    """Disable connector request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class ValidateConnectorRequest(BaseModel):
    """Validate connector request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)


def get_kernel_container(request: Request) -> KernelContainer:
    """Return kernel container."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container


def get_connector_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ConnectorService:
    """Return connector service."""
    return container.connector_service


@router.post("", response_model=ConnectorDefinition)
def create_connector(
    body: ConnectorCreateRequest,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorDefinition:
    """Create connector metadata."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    try:
        return service.create_connector(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{connector_id}", response_model=ConnectorDefinition)
def get_connector(
    connector_id: str,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConnectorDefinition:
    """Return one connector."""
    connector = service.get_connector(connector_id, _scope(scope, actor_context))
    if connector is None:
        raise HTTPException(status_code=404, detail="connector_not_found")
    return connector


@router.get("", response_model=list[ConnectorDefinition])
def list_connectors(
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    connector_type: str | None = None,
) -> list[ConnectorDefinition]:
    """List connectors."""
    return service.list_connectors(
        _scope(scope, actor_context),
        status=status,
        connector_type=connector_type,
    )


@router.post("/{connector_id}/disable", response_model=ConnectorDefinition)
def disable_connector(
    connector_id: str,
    body: DisableConnectorRequest,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorDefinition:
    """Disable one connector."""
    try:
        return service.disable_connector(
            connector_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{connector_id}/validate", response_model=SandboxValidationResult)
def validate_connector(
    connector_id: str,
    body: ValidateConnectorRequest,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SandboxValidationResult:
    """Validate connector metadata without connecting."""
    try:
        return service.validate_connector(connector_id, body.scope or actor_context.security_scope)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]
