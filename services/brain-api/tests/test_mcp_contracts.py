"""MCP contract validation tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.mcp import (
    MCPCapabilityMapping,
    MCPInvocationRequest,
    MCPServerRecord,
    MCPSyncRequest,
)


def test_mcp_server_record_validates_transport_type() -> None:
    with pytest.raises(ValidationError):
        MCPServerRecord(**{**server_payload(), "transport_type": "ftp"})


def test_mcp_server_record_rejects_secret_config() -> None:
    with pytest.raises(ValidationError):
        MCPServerRecord(**{**server_payload(), "config": {"api_key": "nope"}})


def test_mcp_server_record_rejects_dangerous_stdio_command() -> None:
    with pytest.raises(ValidationError):
        MCPServerRecord(
            **{
                **server_payload(),
                "transport_type": "stdio",
                "endpoint_ref": "run; rm -rf",
            }
        )


def test_mcp_mapping_validates_risk_level() -> None:
    with pytest.raises(ValidationError):
        MCPCapabilityMapping(**{**mapping_payload(), "risk_level": "unknown"})


def test_mcp_sync_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        MCPSyncRequest(mcp_server_id="mcp-1", owner_scope=[])


def test_mcp_invocation_request_validates_mode() -> None:
    with pytest.raises(ValidationError):
        MCPInvocationRequest(**{**invocation_payload(), "mode": "background"})


def server_payload() -> dict[str, object]:
    return {
        "mcp_server_id": "mcp-server-1",
        "server_name": "test-server",
        "transport_type": "in_memory_fake",
        "endpoint_ref": None,
        "status": "registered",
        "health_status": "unknown",
        "config": {},
        "owner_scope": ["workspace:main"],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "last_health_check_at": None,
        "disabled_at": None,
    }


def mapping_payload() -> dict[str, object]:
    return {
        "mapping_id": "mapping-1",
        "mcp_server_id": "mcp-server-1",
        "mcp_tool_name": "echo",
        "capability_id": "mcp.test.echo",
        "module_id": "mcp.test",
        "risk_level": "medium",
        "status": "active",
        "input_schema": {},
        "output_schema": {},
        "permissions_required": [],
        "memory_read_scopes": [],
        "memory_write_scopes": [],
        "metadata": {},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "disabled_at": None,
    }


def invocation_payload() -> dict[str, object]:
    return {
        "mcp_invocation_id": None,
        "invocation_id": "invocation-1",
        "mcp_server_id": "mcp-server-1",
        "mcp_tool_name": "echo",
        "capability_id": "mcp.test.echo",
        "trace_id": None,
        "execution_id": None,
        "step_run_id": None,
        "actor_id": None,
        "workspace_id": None,
        "mode": "dry_run",
        "payload": {},
        "approval_present": False,
        "metadata": {},
    }
