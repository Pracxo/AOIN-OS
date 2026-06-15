"""MCP autonomy integration tests."""

from aion_brain.contracts.mcp import (
    MCPInvocationRequest,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
)
from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_mcp_contracts import invocation_payload
from tests.test_mcp_service import make_service, server


def test_mcp_invocation_blocks_when_autonomy_denies() -> None:
    """MCP tool invocation returns a structured blocked result."""
    service = make_service(enabled=True)
    service.register_server(MCPServerRegistrationRequest(server=server(), activate=True))
    service.sync_tools(
        MCPSyncRequest(
            mcp_server_id="mcp-server-1",
            dry_run=False,
            auto_register_capabilities=True,
            default_risk_level="low",
            default_permissions_required=[],
            owner_scope=["workspace:main"],
        )
    )
    service._autonomy_governor = FakeAutonomyGovernor(allow=False)  # noqa: SLF001

    result = service.invoke(
        MCPInvocationRequest(
            **{**invocation_payload(), "capability_id": "mcp.test-server.echo"}
        )
    )

    assert result.status == "blocked_by_policy"
    assert result.error["reason"] == "autonomy_denied"
