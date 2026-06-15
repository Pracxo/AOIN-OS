"""Kernel app factory tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_app_factory_stores_container_and_keeps_health_contract() -> None:
    container = kernel_container()
    app = create_app(container)
    assert app.state.kernel_container is container
    assert TestClient(app).get("/health").json() == {
        "status": "ok",
        "service": "aion-brain-api",
        "version": "0.1.0",
    }
