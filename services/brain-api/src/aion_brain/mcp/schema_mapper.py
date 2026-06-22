"""Map MCP tool descriptors into AION capability contracts."""

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.mcp import (
    MCPCapabilityMapping,
    MCPRiskLevel,
    MCPServerRecord,
    MCPToolDescriptor,
)
from aion_brain.mcp.security import sanitize_mcp_tool_name


def tool_to_capability_mapping(
    server: MCPServerRecord,
    tool: MCPToolDescriptor,
    defaults: dict[str, Any],
) -> MCPCapabilityMapping:
    """Create an AION-owned capability mapping from one MCP tool descriptor."""
    safe_server = sanitize_mcp_tool_name(server.server_name)
    safe_tool = sanitize_mcp_tool_name(tool.name)
    risk_level = cast(MCPRiskLevel, defaults.get("risk_level", "medium"))
    permissions = _dedupe(
        [
            "capability.invoke",
            "mcp.tool.invoke",
            *list(defaults.get("permissions_required", [])),
        ]
    )
    now = datetime.now(UTC)
    capability_id = f"mcp.{safe_server}.{safe_tool}"
    return MCPCapabilityMapping(
        mapping_id=f"mapping-{server.mcp_server_id}-{safe_tool}",
        mcp_server_id=server.mcp_server_id,
        mcp_tool_name=tool.name,
        capability_id=capability_id,
        module_id=f"mcp.{safe_server}",
        risk_level=risk_level,
        status="active",
        input_schema=tool.input_schema,
        output_schema=tool.output_schema or {},
        permissions_required=permissions,
        memory_read_scopes=list(defaults.get("memory_read_scopes", [])),
        memory_write_scopes=list(defaults.get("memory_write_scopes", [])),
        metadata={
            "mcp_server_id": server.mcp_server_id,
            "mcp_tool_name": tool.name,
            "transport_type": server.transport_type,
        },
        created_at=now,
        updated_at=now,
        disabled_at=None,
    )


def mapping_to_capability_definition(mapping: MCPCapabilityMapping) -> dict[str, Any]:
    """Return a dict compatible with AION's current capability manifest contract."""
    return {
        "capability_id": mapping.capability_id,
        "name": mapping.capability_id,
        "description": f"MCP tool mapping for {mapping.mcp_tool_name}.",
        "input_schema": mapping.input_schema,
        "output_schema": mapping.output_schema,
        "risk_level": mapping.risk_level,
        "permissions_required": mapping.permissions_required,
        "memory_read_scopes": mapping.memory_read_scopes,
        "memory_write_scopes": mapping.memory_write_scopes,
        "execution_mode": "sync",
        "timeout_seconds": 15,
        "audit_level": "full",
        "metadata": mapping.metadata,
    }


def mapping_to_capability_manifest(
    server: MCPServerRecord,
    mappings: list[MCPCapabilityMapping],
) -> CapabilityManifest:
    """Create an AION capability manifest from MCP mappings."""
    safe_server = sanitize_mcp_tool_name(server.server_name)
    return CapabilityManifest(
        module_id=f"mcp.{safe_server}",
        version="0.1.0",
        capabilities=[mapping_to_capability_definition(mapping) for mapping in mappings],
        permissions_required=_dedupe(
            permission for mapping in mappings for permission in mapping.permissions_required
        ),
        memory_read_scopes=_dedupe(
            scope for mapping in mappings for scope in mapping.memory_read_scopes
        ),
        memory_write_scopes=_dedupe(
            scope for mapping in mappings for scope in mapping.memory_write_scopes
        ),
        events_subscribed=[],
        events_published=[],
        execution_mode="sync",
    )


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value not in seen:
            seen.add(value)
            result.append(value)
    return result
