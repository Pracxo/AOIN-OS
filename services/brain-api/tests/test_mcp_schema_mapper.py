"""MCP schema mapper tests."""

from aion_brain.contracts.mcp import MCPServerRecord, MCPToolDescriptor
from aion_brain.mcp.schema_mapper import (
    mapping_to_capability_manifest,
    tool_to_capability_mapping,
)
from tests.test_mcp_contracts import server_payload


def test_schema_mapper_creates_generic_capability_id_without_domain_risk() -> None:
    server = MCPServerRecord(**{**server_payload(), "server_name": "Test Server"})
    tool = MCPToolDescriptor(
        name="Echo Tool",
        description="Echo",
        input_schema={"type": "object"},
        output_schema=None,
        annotations={},
        metadata={},
    )

    mapping = tool_to_capability_mapping(server, tool, {"risk_level": "medium"})

    assert mapping.capability_id == "mcp.test-server.echo-tool"
    assert mapping.risk_level == "medium"
    assert "capability.invoke" in mapping.permissions_required
    assert "mcp.tool.invoke" in mapping.permissions_required


def test_schema_mapper_creates_aion_capability_manifest() -> None:
    server = MCPServerRecord(**server_payload())
    tool = MCPToolDescriptor(
        name="echo",
        description="Echo",
        input_schema={},
        output_schema={},
        annotations={},
        metadata={},
    )
    mapping = tool_to_capability_mapping(server, tool, {"risk_level": "low"})

    manifest = mapping_to_capability_manifest(server, [mapping])

    assert manifest.module_id == "mcp.test-server"
    assert manifest.capabilities[0]["capability_id"] == "mcp.test-server.echo"
