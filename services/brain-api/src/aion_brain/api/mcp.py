"""MCP capability protocol adapter API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict

from aion_brain.api.approvals import get_cached_approval_service
from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.capabilities.service import CapabilityService
from aion_brain.config import get_settings
from aion_brain.contracts.mcp import (
    MCPAdapterStatus,
    MCPCapabilityMapping,
    MCPInvocationRequest,
    MCPInvocationResult,
    MCPServerHealth,
    MCPServerRecord,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
    MCPSyncResponse,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.mcp.compat import MCPCompat
from aion_brain.mcp.repository import MCPRepository
from aion_brain.mcp.service import MCPPolicyDenied, MCPService
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/mcp", tags=["mcp"])


class DisableMCPServerRequest(BaseModel):
    """Request to disable an MCP server."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


def get_mcp_service(request: Request) -> MCPService:
    """Return the kernel MCP service when available."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.mcp_service
    settings = get_settings()
    return get_cached_mcp_service(
        settings.database_url,
        settings.opa_url,
        settings.mcp_enabled,
        settings.mcp_allow_network,
        settings.mcp_allow_stdio,
        settings.mcp_timeout_seconds,
        settings.mcp_default_risk_level,
        settings.mcp_auto_register_capabilities,
    )


@lru_cache
def get_cached_mcp_service(
    database_url: str,
    opa_url: str,
    mcp_enabled: bool,
    mcp_allow_network: bool,
    mcp_allow_stdio: bool,
    mcp_timeout_seconds: float,
    mcp_default_risk_level: str,
    mcp_auto_register_capabilities: bool,
) -> MCPService:
    """Build a cached MCP service outside the kernel container."""
    settings = get_settings().model_copy(
        update={
            "database_url": database_url,
            "opa_url": opa_url,
            "mcp_enabled": mcp_enabled,
            "mcp_allow_network": mcp_allow_network,
            "mcp_allow_stdio": mcp_allow_stdio,
            "mcp_timeout_seconds": mcp_timeout_seconds,
            "mcp_default_risk_level": mcp_default_risk_level,
            "mcp_auto_register_capabilities": mcp_auto_register_capabilities,
        }
    )
    registry = CapabilityRegistry()
    return MCPService(
        mcp_repository=MCPRepository(database_url),
        capability_service=CapabilityService(registry),
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=None,
        settings=settings,
        compat=MCPCompat(),
        approval_service=get_cached_approval_service(
            database_url,
            opa_url,
            settings.risk_engine_enabled,
            settings.guardrails_enabled,
            settings.approvals_enabled,
            settings.approval_default_expiry_hours,
            settings.high_risk_requires_approval,
            settings.critical_risk_blocks_by_default,
        ),
    )


@router.get("/status", response_model=MCPAdapterStatus)
def get_mcp_status(
    service: Annotated[MCPService, Depends(get_mcp_service)],
) -> MCPAdapterStatus:
    """Return MCP adapter status."""
    return service.status()


@router.post("/servers", response_model=MCPServerRecord)
def register_mcp_server(
    request: MCPServerRegistrationRequest,
    service: Annotated[MCPService, Depends(get_mcp_service)],
) -> MCPServerRecord:
    """Register an MCP server."""
    try:
        return service.register_server(request)
    except MCPPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/servers", response_model=list[MCPServerRecord])
def list_mcp_servers(
    service: Annotated[MCPService, Depends(get_mcp_service)],
    status: Annotated[str | None, Query()] = None,
) -> list[MCPServerRecord]:
    """List MCP servers."""
    return service.list_servers(status)


@router.get("/servers/{mcp_server_id}", response_model=MCPServerRecord)
def get_mcp_server(
    mcp_server_id: str,
    service: Annotated[MCPService, Depends(get_mcp_service)],
) -> MCPServerRecord:
    """Return one MCP server."""
    server = service.get_server(mcp_server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="mcp_server_not_found")
    return server


@router.post("/servers/{mcp_server_id}/disable", response_model=MCPServerRecord)
def disable_mcp_server(
    mcp_server_id: str,
    request: DisableMCPServerRequest,
    service: Annotated[MCPService, Depends(get_mcp_service)],
) -> MCPServerRecord:
    """Disable an MCP server."""
    try:
        return service.disable_server(mcp_server_id, request.reason)
    except MCPPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="mcp_server_not_found") from exc


@router.post("/servers/{mcp_server_id}/health-check", response_model=MCPServerHealth)
def health_check_mcp_server(
    mcp_server_id: str,
    service: Annotated[MCPService, Depends(get_mcp_service)],
) -> MCPServerHealth:
    """Run an MCP server health check."""
    return service.health_check(mcp_server_id)


@router.post("/sync", response_model=MCPSyncResponse)
def sync_mcp_tools(
    request: MCPSyncRequest,
    service: Annotated[MCPService, Depends(get_mcp_service)],
) -> MCPSyncResponse:
    """Discover and optionally map MCP tools."""
    return service.sync_tools(request)


@router.get("/mappings", response_model=list[MCPCapabilityMapping])
def list_mcp_mappings(
    service: Annotated[MCPService, Depends(get_mcp_service)],
    mcp_server_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[MCPCapabilityMapping]:
    """List MCP capability mappings."""
    return service.list_mappings(mcp_server_id, status)


@router.post("/invoke", response_model=MCPInvocationResult)
def invoke_mcp_tool(
    request: MCPInvocationRequest,
    service: Annotated[MCPService, Depends(get_mcp_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MCPInvocationResult:
    """Invoke or dry-run an MCP tool through the AION boundary."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
        }
    )
    return service.invoke(enriched)


def _policy_denied(exc: MCPPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "reason": exc.decision.reason,
            "decision_id": exc.decision.decision_id,
            "constraints": exc.decision.constraints,
        },
    )
