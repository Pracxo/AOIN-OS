from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_local_auth_api_exposes_dev_only_contracts() -> None:
    client = TestClient(create_app(kernel_container()))

    roles = client.get("/brain/local-auth/roles", params={"scope": "workspace:main"})
    assert roles.status_code == 200
    assert {item["role"] for item in roles.json()} >= {"viewer", "operator", "reviewer"}

    simulation = client.post(
        "/brain/local-auth/simulate",
        json={
            "actor_id": "local.operator",
            "workspace_id": "local",
            "roles": ["operator"],
            "owner_scope": ["workspace:main"],
        },
    )
    assert simulation.status_code == 200
    context = simulation.json()
    assert context["production_auth"] is False
    assert context["credentials_present"] is False

    filtered = client.post(
        "/brain/local-auth/filter-console",
        json={
            "view_model": {
                "console_view_model_id": "console-view-1",
                "view": "overview",
                "status": "ready",
                "sections": [],
                "global_actions": [{"action_key": "inspect_refs", "action_type": "read"}],
                "forbidden_actions": [{"action_key": "activate_module"}],
            },
            "auth_context": context,
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["read_only"] is True

    audit = client.post(
        "/brain/local-auth/audit",
        json={"owner_scope": ["workspace:main"], "include_examples": True},
    )
    assert audit.status_code == 200
    assert audit.json()["status"] == "passed"

    status = client.get("/brain/local-auth/status", params={"scope": "workspace:main"})
    assert status.status_code == 200
    assert status.json()["production_auth_enabled"] is False
    assert status.json()["sessions_enabled"] is False
