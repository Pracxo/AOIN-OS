"""Command Bus API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.commands.bus import CommandBus
from aion_brain.contracts.commands import (
    BrainCommand,
    CommandDispatchRequest,
    CommandDispatchResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/commands", tags=["commands"])


class CancelCommandRequest(BaseModel):
    """Command cancellation body."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)


def get_command_bus(request: Request) -> CommandBus:
    """Return the configured command bus."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.command_bus
    raise RuntimeError("command_bus_unavailable")


@router.post("", response_model=CommandDispatchResult)
def dispatch_command(
    request: CommandDispatchRequest,
    command_bus: Annotated[CommandBus, Depends(get_command_bus)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CommandDispatchResult:
    """Dispatch one generic Brain command."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "trace_id": request.trace_id or actor_context.trace_id,
            "correlation_id": request.correlation_id or actor_context.correlation_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return command_bus.dispatch(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{command_id}", response_model=BrainCommand)
def get_command(
    command_id: str,
    command_bus: Annotated[CommandBus, Depends(get_command_bus)],
) -> BrainCommand:
    """Return one command."""
    command = command_bus.get(command_id)
    if command is None:
        raise HTTPException(status_code=404, detail="command_not_found")
    return command


@router.get("", response_model=list[BrainCommand])
def list_commands(
    command_bus: Annotated[CommandBus, Depends(get_command_bus)],
    status: Annotated[str | None, Query()] = None,
    command_type: Annotated[str | None, Query()] = None,
    trace_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[BrainCommand]:
    """List commands."""
    return command_bus.list_commands(
        status=status,
        command_type=command_type,
        trace_id=trace_id,
        limit=limit,
    )


@router.post("/{command_id}/cancel", response_model=BrainCommand)
def cancel_command(
    command_id: str,
    body: CancelCommandRequest,
    command_bus: Annotated[CommandBus, Depends(get_command_bus)],
) -> BrainCommand:
    """Cancel one command."""
    try:
        return command_bus.cancel(command_id, body.reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
