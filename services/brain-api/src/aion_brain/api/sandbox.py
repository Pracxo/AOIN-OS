"""Sandbox Control Plane API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.sandbox import (
    RuntimePermissionGrant,
    RuntimePermissionGrantRequest,
    SandboxProfile,
    SandboxProfileCreateRequest,
    SandboxRunRequest,
    SandboxRunResult,
    SandboxValidationResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.sandbox.service import SandboxService

router = APIRouter(prefix="/brain/sandbox", tags=["sandbox"])


class DisableRequest(BaseModel):
    """Disable request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class ValidateRequest(BaseModel):
    """Validate request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)


class RevokeRuntimePermissionRequest(BaseModel):
    """Revoke runtime permission request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


def get_kernel_container(request: Request) -> KernelContainer:
    """Return the kernel container."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container


def get_sandbox_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SandboxService:
    """Return sandbox service."""
    return container.sandbox_service


@router.post("/profiles", response_model=SandboxProfile)
def create_profile(
    body: SandboxProfileCreateRequest,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SandboxProfile:
    """Create a sandbox profile."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    try:
        return service.create_profile(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/profiles/{sandbox_profile_id}", response_model=SandboxProfile)
def get_profile(
    sandbox_profile_id: str,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SandboxProfile:
    """Return one sandbox profile."""
    profile = service.get_profile(sandbox_profile_id, _scope(scope, actor_context))
    if profile is None:
        raise HTTPException(status_code=404, detail="sandbox_profile_not_found")
    return profile


@router.get("/profiles", response_model=list[SandboxProfile])
def list_profiles(
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
) -> list[SandboxProfile]:
    """List sandbox profiles."""
    return service.list_profiles(_scope(scope, actor_context), status=status)


@router.post("/profiles/{sandbox_profile_id}/disable", response_model=SandboxProfile)
def disable_profile(
    sandbox_profile_id: str,
    body: DisableRequest,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SandboxProfile:
    """Disable one profile."""
    try:
        return service.disable_profile(
            sandbox_profile_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/profiles/{sandbox_profile_id}/validate", response_model=SandboxValidationResult)
def validate_profile(
    sandbox_profile_id: str,
    body: ValidateRequest,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SandboxValidationResult:
    """Validate one profile."""
    try:
        return service.validate_profile(
            sandbox_profile_id,
            body.scope or actor_context.security_scope,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/run", response_model=SandboxRunResult)
def run_sandbox(
    body: SandboxRunRequest,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SandboxRunResult:
    """Run sandbox control-plane validation or dry-run."""
    request = body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "trace_id": body.trace_id or actor_context.trace_id,
        }
    )
    try:
        return service.run(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/runtime-permissions", response_model=RuntimePermissionGrant)
def grant_runtime_permission(
    body: RuntimePermissionGrantRequest,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RuntimePermissionGrant:
    """Grant runtime permissions."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "granted_by": body.granted_by or actor_context.actor_id,
        }
    )
    try:
        return service.grant_runtime_permission(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runtime-permissions", response_model=list[RuntimePermissionGrant])
def list_runtime_permissions(
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    target_type: str | None = None,
    target_id: str | None = None,
    status: str | None = None,
) -> list[RuntimePermissionGrant]:
    """List runtime permission grants."""
    return service.list_runtime_permissions(
        target_type=target_type,
        target_id=target_id,
        status=status,
    )


@router.post(
    "/runtime-permissions/{runtime_permission_id}/revoke",
    response_model=RuntimePermissionGrant,
)
def revoke_runtime_permission(
    runtime_permission_id: str,
    body: RevokeRuntimePermissionRequest,
    service: Annotated[SandboxService, Depends(get_sandbox_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RuntimePermissionGrant:
    """Revoke runtime permissions."""
    try:
        return service.revoke_runtime_permission(
            runtime_permission_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]
