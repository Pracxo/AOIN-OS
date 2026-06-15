"""MCP repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.mcp import (
    MCPCapabilityMapping,
    MCPInvocationResult,
    MCPServerHealth,
    MCPServerRecord,
    MCPSyncResponse,
)
from aion_brain.mcp.repository import MCPRepository
from tests.test_mcp_contracts import mapping_payload, server_payload


def test_mcp_repository_persists_server_mapping_sync_and_invocation() -> None:
    repository = MCPRepository(engine=sqlite_engine())
    server = repository.create_server(MCPServerRecord(**server_payload()))
    mapping = repository.upsert_mapping(MCPCapabilityMapping(**mapping_payload()))

    repository.record_sync(
        MCPSyncResponse(
            sync_id="sync-1",
            mcp_server_id=server.mcp_server_id,
            dry_run=False,
            discovered_tools=1,
            mapped_capabilities=1,
            skipped=0,
            failed=0,
            mappings=[mapping],
            errors=[],
            status="completed",
            reason=None,
            created_at=server.created_at,
        )
    )
    repository.record_invocation(
        MCPInvocationResult(
            mcp_invocation_id="mcp-invocation-1",
            invocation_id="invocation-1",
            mcp_server_id=server.mcp_server_id,
            mcp_tool_name="echo",
            capability_id=mapping.capability_id,
            status="dry_run",
            output={},
            error={},
            latency_ms=0,
            policy_decision_id=None,
            created_at=server.created_at,
        )
    )

    assert repository.get_server(server.mcp_server_id) == server
    assert repository.get_mapping_by_capability(mapping.capability_id) == mapping
    assert repository.get_mapping_by_tool(server.mcp_server_id, "echo") == mapping


def test_mcp_repository_disables_server_and_updates_health() -> None:
    repository = MCPRepository(engine=sqlite_engine())
    server = repository.create_server(MCPServerRecord(**server_payload()))

    health = MCPServerHealth(
        mcp_server_id=server.mcp_server_id,
        status="healthy",
        latency_ms=0,
        details={},
        checked_at=server.created_at,
    )

    assert repository.update_server_health(server.mcp_server_id, health).health_status == "healthy"
    assert repository.disable_server(server.mcp_server_id, "done").status == "disabled"


def sqlite_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
