from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_auth_runtime_api_endpoints_work_without_login_flows() -> None:
    client = TestClient(create_app(kernel_container()))
    payload = {
        "issuer": "mock.local",
        "subject": "local.operator",
        "roles": ["operator"],
        "owner_scope": ["workspace:main"],
        "claims": {"claim_set": "local_demo"},
    }

    status = client.get("/brain/auth-runtime/status", params={"scope": "workspace:main"})
    preview = client.post("/brain/auth-runtime/mock-claims/preview", json=payload)
    audit = client.post(
        "/brain/auth-runtime/audit",
        json={"owner_scope": ["workspace:main"], "include_examples": True},
    )

    assert status.status_code == 200
    assert status.json()["production_auth_enabled"] is False
    assert status.json()["auth_runtime_enabled"] is False
    assert preview.status_code == 200
    assert preview.json()["production_identity"] is False
    assert preview.json()["token_present"] is False
    assert audit.status_code == 200
    assert audit.json()["mock_only"] is True
