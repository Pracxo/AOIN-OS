from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_operator_console_api_list_views_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.get("/brain/operator-console/views", params={"scope": "workspace:main"})

    assert response.status_code == 200
    assert any(item["view"] == "overview" for item in response.json())


def test_operator_console_api_view_model_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/operator-console/view-model",
        json={"view": "overview", "owner_scope": ["workspace:main"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["read_only"] is True
    assert payload["redaction_applied"] is True
    assert payload["forbidden_actions"]


def test_operator_console_api_audit_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/operator-console/audit",
        json={"owner_scope": ["workspace:main"], "include_examples": True},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "passed"


def test_operator_console_api_workflows_and_demo_map_work() -> None:
    client = TestClient(create_app(kernel_container()))

    workflows = client.get(
        "/brain/operator-console/workflows",
        params={"scope": "workspace:main"},
    )
    demo = client.get("/brain/operator-console/demo-map", params={"scope": "workspace:main"})

    assert workflows.status_code == 200
    assert workflows.json()[0]["status"] == "read_only"
    assert demo.status_code == 200
    assert demo.json()["read_only"] is True
