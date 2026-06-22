"""Capability Registry and Runtime Gateway API."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.dependencies import get_capability_runtime_gateway, get_capability_service
from aion_brain.capabilities.service import CapabilityService
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.modules import (
    CapabilityBindingRequest,
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    CapabilityRuntimeBinding,
)
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway

router = APIRouter(prefix="/brain/capabilities", tags=["capabilities"])


class LegacyCapabilityInvokeRequest(BaseModel):
    """Backward-compatible capability invocation payload."""

    model_config = ConfigDict(extra="allow")

    invocation_id: str | None = None
    trace_id: str | None = None
    execution_id: str | None = None
    step_run_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: str = "dry_run"
    payload: dict[str, Any] = Field(default_factory=dict)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/register", response_model=CapabilityManifest)
def register_capability_manifest(
    manifest: CapabilityManifest,
    service: Annotated[CapabilityService, Depends(get_capability_service)],
) -> CapabilityManifest:
    """Register a capability manifest."""
    return service.register_manifest(manifest)


@router.get("/manifests", response_model=list[CapabilityManifest])
def list_capability_manifests(
    service: Annotated[CapabilityService, Depends(get_capability_service)],
) -> list[CapabilityManifest]:
    """List capability manifests."""
    return service.list_manifests()


@router.get("")
def list_capabilities(
    service: Annotated[CapabilityService, Depends(get_capability_service)],
) -> list[dict[str, object]]:
    """List flattened registered capabilities."""
    return service.list_capabilities()


@router.post("/{capability_id}/bind-runtime", response_model=CapabilityRuntimeBinding)
def bind_capability_runtime(
    capability_id: str,
    request: CapabilityBindingRequest,
    gateway: Annotated[CapabilityRuntimeGateway, Depends(get_capability_runtime_gateway)],
) -> CapabilityRuntimeBinding:
    """Bind a capability to a registered runtime."""
    if request.capability_id != capability_id:
        raise HTTPException(status_code=400, detail="capability_id_mismatch")
    try:
        return gateway.bind_capability(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/invoke", response_model=CapabilityInvocationResult)
def invoke_capability(
    request: CapabilityInvocationRequest,
    gateway: Annotated[CapabilityRuntimeGateway, Depends(get_capability_runtime_gateway)],
) -> CapabilityInvocationResult:
    """Invoke a capability through the runtime gateway."""
    return gateway.invoke(request)


@router.post("/{capability_id}/invoke", response_model=CapabilityInvocationResult)
def invoke_capability_by_id(
    capability_id: str,
    request: LegacyCapabilityInvokeRequest,
    gateway: Annotated[CapabilityRuntimeGateway, Depends(get_capability_runtime_gateway)],
) -> CapabilityInvocationResult:
    """Backward-compatible capability invoke route backed by the runtime gateway."""
    invocation = CapabilityInvocationRequest(
        invocation_id=request.invocation_id
        or f"invocation-{capability_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
        trace_id=request.trace_id,
        execution_id=request.execution_id,
        step_run_id=request.step_run_id,
        capability_id=capability_id,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        mode=request.mode,  # type: ignore[arg-type]
        payload=request.payload,
        approval_present=request.approval_present,
        metadata=request.metadata,
    )
    return gateway.invoke(invocation)
