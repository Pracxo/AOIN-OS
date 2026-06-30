from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_connector_sandbox_api_endpoints_are_preview_only() -> None:
    client = TestClient(create_app(kernel_container()))

    boundary = client.get("/brain/connector-sandbox/boundary")
    rules = client.get("/brain/connector-sandbox/capability-rules")
    readiness = client.post(
        "/brain/connector-sandbox/readiness",
        json={
            "connector_key": "mock.local.preview",
            "owner_scope": ["workspace:main"],
            "requested_capabilities": ["connector.sandbox.readiness.preview"],
        },
    )
    query = client.post(
        "/brain/connector-sandbox/query",
        json={
            "owner_scope": ["workspace:main"],
            "capability": "connector.sandbox.runtime.execute",
        },
    )
    status = client.get("/brain/connector-sandbox/status", params={"scope": "workspace:main"})

    assert boundary.status_code == 200
    assert boundary.json()["runtime_execution_allowed"] is False
    assert boundary.json()["filesystem_access_allowed"] is False
    assert rules.status_code == 200
    assert any(item["rule_key"] == "connector.sandbox.readiness.preview" for item in rules.json())
    assert all(item["runtime_allowed"] is False for item in rules.json())
    assert readiness.status_code == 200
    assert readiness.json()["runtime_execution_allowed"] is False
    assert readiness.json()["network_access_allowed"] is False
    assert query.status_code == 200
    assert query.json()["denial"]["runtime_execution_allowed"] is False
    assert status.status_code == 200
    assert status.json()["connector_sandbox_runtime_execution_enabled"] is False
    assert status.json()["connector_sandbox_network_enabled"] is False
