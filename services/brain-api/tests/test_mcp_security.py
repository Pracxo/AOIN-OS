"""MCP security helper tests."""

import pytest

from aion_brain.config import Settings
from aion_brain.contracts.mcp import MCPServerRecord
from aion_brain.mcp.security import (
    contains_shell_control_chars,
    reject_secret_like_config,
    sanitize_mcp_tool_name,
    validate_mcp_server_security,
)
from tests.test_mcp_contracts import server_payload


def test_mcp_security_blocks_http_and_sse_when_network_disabled() -> None:
    settings = Settings(_env_file=None, AION_MCP_ENABLED=True)

    http = MCPServerRecord(**{**server_payload(), "transport_type": "http"})
    sse = MCPServerRecord(**{**server_payload(), "transport_type": "sse"})

    assert "mcp_network_disabled" in validate_mcp_server_security(http, settings)
    assert "mcp_network_disabled" in validate_mcp_server_security(sse, settings)


def test_mcp_security_blocks_stdio_when_disabled() -> None:
    settings = Settings(_env_file=None, AION_MCP_ENABLED=True)
    server = MCPServerRecord(**{**server_payload(), "transport_type": "stdio"})

    assert "mcp_stdio_disabled" in validate_mcp_server_security(server, settings)


def test_mcp_security_rejects_shell_control_chars_and_secret_config() -> None:
    assert contains_shell_control_chars("tool && other")
    with pytest.raises(ValueError):
        reject_secret_like_config({"private_key": "nope"})
    assert sanitize_mcp_tool_name("Echo Tool!") == "echo-tool"
