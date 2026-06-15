"""Connector Registry API tests."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from aion_brain.api import connectors as connectors_api
from aion_brain.main import app
from tests.sandbox_fakes import connector_request, make_connector_service


def test_connector_apis_work() -> None:
    service = make_connector_service()
    app.dependency_overrides[connectors_api.get_kernel_container] = lambda: SimpleNamespace(
        connector_service=service
    )
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/connectors",
            json=connector_request().model_dump(mode="json"),
        )
        listed = client.get("/brain/connectors", params={"scope": "workspace:main"})
        validated = client.post(
            "/brain/connectors/connector-1/validate",
            json={"scope": ["workspace:main"]},
        )
        disabled = client.post(
            "/brain/connectors/connector-1/disable",
            json={"actor_id": "dev", "reason": "test"},
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert listed.json()[0]["connector_id"] == "connector-1"
    assert validated.json()["status"] == "passed"
    assert disabled.json()["status"] == "disabled"
