"""Health compatibility tests for API hardening."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_health_response_remains_unchanged() -> None:
    response = TestClient(create_app(kernel_container())).get("/health")

    assert response.json() == {
        "status": "ok",
        "service": "aion-brain-api",
        "version": "0.1.0",
    }
