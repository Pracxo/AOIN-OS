"""Health endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from aion_brain.api import health as health_module
from aion_brain.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


def test_health_returns_expected_payload(client: TestClient) -> None:
    """The health endpoint exposes stable scaffold metadata."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "aion-brain-api",
        "version": "0.1.0",
    }


def test_liveness_returns_expected_payload(client: TestClient) -> None:
    """The liveness endpoint exposes process metadata."""
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "service": "aion-brain-api",
        "version": "0.1.0",
    }


def test_readiness_returns_ready_when_checks_pass(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The readiness endpoint reports ready when all checks pass."""
    monkeypatch.setattr(health_module, "check_postgres", lambda database_url: True)
    monkeypatch.setattr(health_module, "check_redis", lambda redis_url: True)
    monkeypatch.setattr(health_module, "check_nats", lambda nats_url: True)
    monkeypatch.setattr(health_module, "check_opa", lambda opa_url: True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "postgres": "ok",
            "redis": "ok",
            "nats": "ok",
            "opa": "ok",
        },
    }


def test_readiness_returns_degraded_when_checks_fail(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The readiness endpoint reports degraded without raising."""
    monkeypatch.setattr(health_module, "check_postgres", lambda database_url: True)
    monkeypatch.setattr(health_module, "check_redis", lambda redis_url: False)
    monkeypatch.setattr(health_module, "check_nats", lambda nats_url: True)
    monkeypatch.setattr(health_module, "check_opa", lambda opa_url: False)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "checks": {
            "postgres": "ok",
            "redis": "fail",
            "nats": "ok",
            "opa": "fail",
        },
    }


def test_readiness_converts_exceptions_to_fail(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Readiness failures never crash the API."""

    def raise_error(_url: str) -> bool:
        raise RuntimeError("dependency unavailable")

    monkeypatch.setattr(health_module, "check_postgres", raise_error)
    monkeypatch.setattr(health_module, "check_redis", lambda redis_url: True)
    monkeypatch.setattr(health_module, "check_nats", lambda nats_url: True)
    monkeypatch.setattr(health_module, "check_opa", lambda opa_url: True)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["postgres"] == "fail"
