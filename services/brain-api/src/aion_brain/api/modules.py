"""Module bus API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.dependencies import get_capability_runtime_gateway
from aion_brain.contracts.modules import (
    ModuleHealthCheck,
    ModuleRuntime,
    ModuleRuntimeRegistrationRequest,
    ModuleRuntimeRegistrationResponse,
)
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway

router = APIRouter(prefix="/brain/modules", tags=["modules"])


@router.post("/runtimes/register", response_model=ModuleRuntimeRegistrationResponse)
def register_runtime(
    request: ModuleRuntimeRegistrationRequest,
    gateway: Annotated[CapabilityRuntimeGateway, Depends(get_capability_runtime_gateway)],
) -> ModuleRuntimeRegistrationResponse:
    """Register a module runtime through the Module Bus."""
    return gateway.register_runtime(request)


@router.get("/runtimes", response_model=list[ModuleRuntime])
def list_runtimes(
    gateway: Annotated[CapabilityRuntimeGateway, Depends(get_capability_runtime_gateway)],
) -> list[ModuleRuntime]:
    """List registered module runtimes."""
    return gateway.list_runtimes()


@router.get("/runtimes/{runtime_id}", response_model=ModuleRuntime)
def get_runtime(
    runtime_id: str,
    gateway: Annotated[CapabilityRuntimeGateway, Depends(get_capability_runtime_gateway)],
) -> ModuleRuntime:
    """Return a registered module runtime."""
    runtime = gateway.get_runtime(runtime_id)
    if runtime is None:
        raise HTTPException(status_code=404, detail="runtime_not_found")
    return runtime


@router.post("/runtimes/{runtime_id}/health-check", response_model=ModuleHealthCheck)
def health_check_runtime(
    runtime_id: str,
    gateway: Annotated[CapabilityRuntimeGateway, Depends(get_capability_runtime_gateway)],
) -> ModuleHealthCheck:
    """Run a runtime health check."""
    return gateway.health_check(runtime_id)
