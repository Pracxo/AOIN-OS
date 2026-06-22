"""Sandbox API tests."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from aion_brain.api import sandbox as sandbox_api
from aion_brain.main import app
from tests.sandbox_fakes import make_sandbox_service, profile_request


def test_sandbox_apis_work() -> None:
    service = make_sandbox_service()
    app.dependency_overrides[sandbox_api.get_kernel_container] = lambda: SimpleNamespace(
        sandbox_service=service
    )
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/sandbox/profiles",
            json=profile_request().model_dump(mode="json"),
        )
        listed = client.get(
            "/brain/sandbox/profiles",
            params={"scope": "workspace:main"},
        )
        validated = client.post(
            "/brain/sandbox/profiles/sandbox-profile-1/validate",
            json={"scope": ["workspace:main"]},
        )
        grant = client.post(
            "/brain/sandbox/runtime-permissions",
            json={
                "runtime_permission_id": "runtime-permission-api",
                "target_type": "capability",
                "target_id": "test.echo",
                "sandbox_profile_id": "sandbox-profile-1",
                "owner_scope": ["workspace:main"],
                "permissions": [{"permission": "runtime.execute", "allowed": True}],
                "secret_refs": [],
                "connector_refs": [],
                "granted_by": "dev",
                "metadata": {},
            },
        )
        run = client.post(
            "/brain/sandbox/run",
            json={
                "sandbox_profile_id": "sandbox-profile-1",
                "target_type": "capability",
                "target_id": "test.echo",
                "mode": "dry_run",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert listed.status_code == 200
    assert listed.json()[0]["sandbox_profile_id"] == "sandbox-profile-1"
    assert validated.json()["status"] == "passed"
    assert grant.json()["status"] == "active"
    assert run.json()["status"] == "dry_run"


def test_sandbox_disable_api_works() -> None:
    service = make_sandbox_service()
    service.create_profile(profile_request())
    app.dependency_overrides[sandbox_api.get_kernel_container] = lambda: SimpleNamespace(
        sandbox_service=service
    )
    try:
        client = TestClient(app)
        response = client.post(
            "/brain/sandbox/profiles/sandbox-profile-1/disable",
            json={"actor_id": "dev", "reason": "test"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"
