from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_connector_credentials_api_endpoints_are_preview_only() -> None:
    client = TestClient(create_app(kernel_container()))

    boundary = client.get("/brain/connector-credentials/boundary")
    lifecycle = client.get("/brain/connector-credentials/lifecycle")
    authorization = client.get("/brain/connector-credentials/authorization")
    readiness = client.post(
        "/brain/connector-credentials/readiness",
        json={
            "connector_key": "mock.local.preview",
            "owner_scope": ["workspace:main"],
            "requested_scopes": ["connector_credentials.readiness.preview"],
        },
    )
    redaction = client.post(
        "/brain/connector-credentials/redaction-preview",
        json={"client_secret": "placeholder", "safe": "visible"},
    )
    query = client.post(
        "/brain/connector-credentials/query",
        json={
            "owner_scope": ["workspace:main"],
            "action_key": "connector.credentials.store",
        },
    )
    status = client.get("/brain/connector-credentials/status", params={"scope": "workspace:main"})

    assert boundary.status_code == 200
    assert boundary.json()["credential_storage_enabled"] is False
    assert boundary.json()["token_storage_enabled"] is False
    assert lifecycle.status_code == 200
    assert any(item["state_key"] == "provisioned_future" for item in lifecycle.json())
    assert authorization.status_code == 200
    assert all(item["credential_access_allowed"] is False for item in authorization.json())
    assert readiness.status_code == 200
    assert readiness.json()["credential_storage_allowed"] is False
    assert readiness.json()["token_storage_allowed"] is False
    assert redaction.status_code == 200
    assert redaction.json()["redaction_applied"] is True
    assert query.status_code == 200
    assert query.json()["denial"]["credential_storage_allowed"] is False
    assert status.status_code == 200
    assert status.json()["connector_credentials_storage_enabled"] is False
    assert status.json()["connector_tokens_storage_enabled"] is False
