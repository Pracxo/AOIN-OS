"""MCP API tests."""

from fastapi.testclient import TestClient

from aion_brain.api.mcp import get_mcp_service
from aion_brain.main import app
from tests.test_mcp_contracts import invocation_payload, server_payload
from tests.test_mcp_service import make_service


def test_mcp_api_status_register_sync_mappings_and_invoke() -> None:
    service = make_service(enabled=True)
    app.dependency_overrides[get_mcp_service] = lambda: service
    try:
        client = TestClient(app)
        status = client.get("/brain/mcp/status")
        register = client.post(
            "/brain/mcp/servers",
            json={"server": jsonable_server(), "activate": True, "discover_tools": False},
        )
        sync = client.post(
            "/brain/mcp/sync",
            json={
                "mcp_server_id": "mcp-server-1",
                "dry_run": False,
                "auto_register_capabilities": True,
                "default_risk_level": "low",
                "default_permissions_required": [],
                "owner_scope": ["workspace:main"],
                "metadata": {},
            },
        )
        mappings = client.get("/brain/mcp/mappings")
        invoke = client.post(
            "/brain/mcp/invoke",
            json={**invocation_payload(), "capability_id": "mcp.test-server.echo"},
        )
    finally:
        app.dependency_overrides.clear()

    assert status.status_code == 200
    assert register.json()["status"] == "active"
    assert sync.json()["mapped_capabilities"] == 3
    assert mappings.json()[0]["capability_id"].startswith("mcp.")
    assert invoke.json()["status"] == "dry_run"


def jsonable_server() -> dict[str, object]:
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in server_payload().items()
    }
