"""MCP compat fake module tests."""

import sys
from types import SimpleNamespace

from aion_brain.contracts.mcp import MCPServerRecord
from aion_brain.mcp.compat import MCPCompat
from tests.test_mcp_contracts import server_payload


def test_mcp_compat_works_with_fake_module(monkeypatch) -> None:
    class FakeClient:
        def __init__(self, endpoint_ref=None, **config):
            self.endpoint_ref = endpoint_ref
            self.config = config

        def list_tools(self):
            return [{"name": "echo", "description": "Echo", "input_schema": {}}]

        def call_tool(self, tool_name, payload):
            return {"tool": tool_name, "payload": payload}

    monkeypatch.setitem(sys.modules, "mcp", SimpleNamespace(Client=FakeClient))
    server = MCPServerRecord(**server_payload())
    compat = MCPCompat()

    client = compat.create_client(server)
    tools = compat.list_tools(client, server)
    output = compat.call_tool(client, server, "echo", {"value": 1})

    assert compat.is_available()
    assert tools[0].name == "echo"
    assert output == {"tool": "echo", "payload": {"value": 1}}
