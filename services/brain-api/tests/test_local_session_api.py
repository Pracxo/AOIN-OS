from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_local_session_api_exposes_read_only_contracts() -> None:
    client = TestClient(create_app(kernel_container()))
    payload = {
        "actor_id": "local.operator",
        "workspace_id": "local",
        "roles": ["operator"],
        "owner_scope": ["workspace:main"],
    }

    preview = client.post("/brain/local-session/preview", json=payload)
    assert preview.status_code == 200
    assert preview.json()["read_only"] is True
    assert preview.json()["token_issued"] is False

    context = client.post("/brain/local-session/context", json=payload)
    assert context.status_code == 200
    assert context.json()["write_allowed"] is False

    status = client.get("/brain/local-session/status", params={"scope": "workspace:main"})
    assert status.status_code == 200
    assert status.json()["production_session"] is False

    boundary = client.post(
        "/brain/local-session/boundary-check",
        json={"scope": ["workspace:main"], "created_by": "local.operator"},
    )
    assert boundary.status_code == 200
    assert boundary.json()["status"] == "passed"

    audit = client.post(
        "/brain/local-session/audit",
        json={"owner_scope": ["workspace:main"], "include_examples": True},
    )
    assert audit.status_code == 200
    assert audit.json()["status"] == "passed"
