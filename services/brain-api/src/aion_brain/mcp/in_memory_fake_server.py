"""Deterministic in-memory MCP fake server for tests and local demos."""

from copy import deepcopy
from typing import Any

from aion_brain.contracts.mcp import MCPToolDescriptor


class InMemoryFakeMCPServer:
    """Generic fake MCP server with deterministic local tools."""

    def list_tools(self) -> list[MCPToolDescriptor]:
        """Return generic tool descriptors."""
        return [
            MCPToolDescriptor(
                name="echo",
                description="Return the provided payload.",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                annotations={},
                metadata={"fake": True},
            ),
            MCPToolDescriptor(
                name="describe_payload",
                description="Describe the shape of the provided payload.",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                annotations={},
                metadata={"fake": True},
            ),
            MCPToolDescriptor(
                name="validate_payload",
                description="Validate that the provided payload is an object.",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                annotations={},
                metadata={"fake": True},
            ),
        ]

    def call_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call a deterministic fake tool."""
        if tool_name == "echo":
            return {"echo": deepcopy(payload)}
        if tool_name == "describe_payload":
            return {
                "keys": sorted(payload.keys()),
                "field_count": len(payload),
                "types": {key: type(value).__name__ for key, value in sorted(payload.items())},
            }
        if tool_name == "validate_payload":
            return {"valid": isinstance(payload, dict), "error_count": 0}
        raise KeyError(tool_name)
