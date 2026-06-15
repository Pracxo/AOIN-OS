"""MCP capability protocol adapter."""

from typing import Any

from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.mcp import MCPInvocationRequest
from aion_brain.mcp.schema_mapper import mapping_to_capability_manifest


class MCPAdapter:
    """Adapter boundary for MCP capability interoperability."""

    def __init__(self, mcp_service: object | None = None) -> None:
        self._mcp_service = mcp_service

    def list_capabilities(self) -> list[CapabilityManifest]:
        """List MCP-derived AION capability manifests."""
        if self._mcp_service is None:
            return []
        list_servers = getattr(self._mcp_service, "list_servers", None)
        list_mappings = getattr(self._mcp_service, "list_mappings", None)
        if not callable(list_servers) or not callable(list_mappings):
            return []
        manifests: list[CapabilityManifest] = []
        for server in list_servers("active"):
            mappings = list_mappings(getattr(server, "mcp_server_id", ""), "active")
            if mappings:
                manifests.append(mapping_to_capability_manifest(server, mappings))
        return manifests

    def invoke(self, capability_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dry-run invoke an MCP capability through MCPService when configured."""
        if self._mcp_service is None:
            return {"status": "not_implemented", "reason": "mcp_service_not_configured"}
        get_mapping = getattr(self._mcp_service, "get_mapping_by_capability", None)
        invoke = getattr(self._mcp_service, "invoke", None)
        if not callable(get_mapping) or not callable(invoke):
            return {"status": "not_implemented", "reason": "mcp_service_unavailable"}
        mapping = get_mapping(capability_id)
        if mapping is None:
            return {"status": "tool_not_found", "reason": "mcp_mapping_not_found"}
        result = invoke(
            MCPInvocationRequest(
                mcp_invocation_id=None,
                invocation_id=None,
                mcp_server_id=mapping.mcp_server_id,
                mcp_tool_name=mapping.mcp_tool_name,
                capability_id=capability_id,
                trace_id=None,
                execution_id=None,
                step_run_id=None,
                actor_id=None,
                workspace_id=None,
                mode="dry_run",
                payload=payload,
                approval_present=False,
                metadata={},
            )
        )
        return {"status": result.status, "output": result.output, "error": result.error}
