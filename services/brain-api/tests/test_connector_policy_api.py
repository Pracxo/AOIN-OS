from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_connector_policy_api_endpoints_are_dry_run_only() -> None:
    client = TestClient(create_app(kernel_container()))

    catalog = client.get("/brain/connector-policy/catalog")
    matrix = client.get("/brain/connector-policy/matrix")
    dry_run = client.post(
        "/brain/connector-policy/dry-run",
        json={
            "connector_key": "mock.local.preview",
            "role": "operator",
            "requested_action_key": "connector_policy.dry_run",
            "owner_scope": ["workspace:main"],
        },
    )
    traceability = client.post(
        "/brain/connector-policy/traceability/query",
        json={"connector_key": "mock.local.preview", "owner_scope": ["workspace:main"]},
    )
    status = client.get("/brain/connector-policy/status", params={"scope": "workspace:main"})

    assert catalog.status_code == 200
    assert any(item["action_key"] == "connector_policy.dry_run" for item in catalog.json())
    assert matrix.status_code == 200
    assert all(item["runtime_allowed"] is False for item in matrix.json())
    assert dry_run.status_code == 200
    assert dry_run.json()["runtime_allowed"] is False
    assert dry_run.json()["external_call_allowed"] is False
    assert traceability.status_code == 200
    assert traceability.json()
    assert status.status_code == 200
    assert status.json()["connector_policy_runtime_allow_enabled"] is False

