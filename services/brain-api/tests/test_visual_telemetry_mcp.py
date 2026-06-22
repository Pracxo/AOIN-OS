"""MCP visual telemetry contract tests."""

from aion_brain.contracts.mcp import MCPServerRegistrationRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from tests.test_mcp_service import FakeTelemetry, make_service, server


def test_visual_telemetry_accepts_mcp_events() -> None:
    telemetry = FakeTelemetry()
    service = make_service(enabled=True, telemetry=telemetry)

    service.register_server(MCPServerRegistrationRequest(server=server(), activate=True))

    assert isinstance(telemetry.events[0], VisualTelemetryEvent)
    assert telemetry.events[0].event_type == "mcp_server_registered"
    assert telemetry.events[0].node_type == "server"
