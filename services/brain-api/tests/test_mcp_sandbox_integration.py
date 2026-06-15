"""MCP sandbox integration tests."""

from types import SimpleNamespace

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.capabilities.service import CapabilityService
from aion_brain.config import Settings
from aion_brain.contracts.mcp import (
    MCPInvocationRequest,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
)
from aion_brain.mcp.repository import MCPRepository
from aion_brain.mcp.service import MCPService
from tests.sandbox_fakes import FakePolicyAdapter, sqlite_engine
from tests.test_mcp_contracts import invocation_payload, server_payload


class FailingSandbox:
    """Sandbox fake that blocks MCP runs."""

    def has_active_grant(self, **kwargs: object) -> bool:
        return True

    def run(self, request: object) -> object:
        return SimpleNamespace(status="failed", sandbox_run_id="sandbox-run-1")


def test_mcp_service_blocks_when_sandbox_validation_fails() -> None:
    service = MCPService(
        mcp_repository=MCPRepository(engine=sqlite_engine()),
        capability_service=CapabilityService(CapabilityRegistry()),
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=None,
        settings=Settings(_env_file=None, AION_MCP_ENABLED=True),
        sandbox_service=FailingSandbox(),
    )
    service.register_server(
        MCPServerRegistrationRequest(server=server_payload(), activate=True)
    )
    service.sync_tools(
        MCPSyncRequest(
            mcp_server_id="mcp-server-1",
            dry_run=False,
            auto_register_capabilities=True,
            owner_scope=["workspace:main"],
        )
    )

    payload = {
        **invocation_payload(),
        "capability_id": "mcp.test-server.echo",
        "mode": "controlled",
        "approval_present": True,
        "metadata": {"sandbox_profile_id": "sandbox-profile-1"},
    }
    result = service.invoke(MCPInvocationRequest(**payload))

    assert result.status == "blocked_by_policy"
    assert result.error["reason"] == "sandbox_validation_failed"
