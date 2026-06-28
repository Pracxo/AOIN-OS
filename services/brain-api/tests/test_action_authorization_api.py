from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_action_authorization_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))
    payload = {
        "actor_id": "local.operator",
        "workspace_id": "local",
        "roles": ["operator"],
        "owner_scope": ["workspace:main"],
        "action_key": "operator.review",
        "action_type": "generic",
        "target_type": "generic",
    }

    authorize = client.post("/brain/action-authorization/authorize", json=payload)
    audit = client.post(
        "/brain/action-authorization/audit",
        json={"owner_scope": ["workspace:main"], "include_examples": True},
    )
    status = client.get("/brain/action-authorization/status", params={"scope": "workspace:main"})

    assert authorize.status_code == 200
    assert authorize.json()["decision"] == "allow_dry_run_preview"
    assert authorize.json()["execution_allowed"] is False
    assert audit.status_code == 200
    assert audit.json()["execution_blocked"] is True
    assert status.status_code == 200
    assert status.json()["execution_allowed"] is False
