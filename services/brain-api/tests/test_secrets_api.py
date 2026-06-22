"""Secret Reference Vault API tests."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from aion_brain.api import secrets as secrets_api
from aion_brain.main import app
from tests.sandbox_fakes import make_secret_service, secret_request


def test_secret_ref_apis_work() -> None:
    service = make_secret_service()
    app.dependency_overrides[secrets_api.get_kernel_container] = lambda: SimpleNamespace(
        secret_ref_service=service
    )
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/secret-refs",
            json=secret_request().model_dump(mode="json"),
        )
        listed = client.get("/brain/secret-refs", params={"scope": "workspace:main"})
        rotated = client.post(
            "/brain/secret-refs/secret-ref-1/rotate-metadata",
            json={"actor_id": "dev", "metadata": {"rotation_marker": "updated"}},
        )
        disabled = client.post(
            "/brain/secret-refs/secret-ref-1/disable",
            json={"actor_id": "dev", "reason": "test"},
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert listed.json()[0]["secret_ref_id"] == "secret-ref-1"
    assert rotated.json()["metadata"]["rotation_marker"] == "updated"
    assert disabled.json()["status"] == "disabled"
