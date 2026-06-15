"""Kernel API tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_kernel_api_endpoints_work() -> None:
    client = TestClient(create_app(kernel_container()))
    assert client.get("/brain/kernel/status").status_code == 200
    assert client.get("/brain/kernel/boot/latest").status_code == 200
    assert client.get("/brain/kernel/services").status_code == 200
    assert client.get("/brain/kernel/adapters").status_code == 200
    assert client.get("/brain/kernel/contracts").status_code == 200
    assert client.post("/brain/kernel/boundary-check").status_code == 200
    response = client.post(
        "/brain/kernel/self-test",
        json={"scope": ["workspace:test"], "dry_run": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "passed"
    assert client.get("/brain/kernel/self-test/latest").status_code == 200
