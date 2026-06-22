"""Health endpoint resilience integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.api import health as health_module
from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_health_ready_contract_remains_dependency_readiness_only(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(health_module, "check_postgres", lambda database_url: True)
    monkeypatch.setattr(health_module, "check_redis", lambda redis_url: True)
    monkeypatch.setattr(health_module, "check_nats", lambda nats_url: True)
    monkeypatch.setattr(health_module, "check_opa", lambda opa_url: True)
    client = TestClient(create_app(kernel_container()))

    payload = client.get("/health/ready").json()

    assert payload == {
        "status": "ready",
        "checks": {
            "postgres": "ok",
            "redis": "ok",
            "nats": "ok",
            "opa": "ok",
        },
    }
    assert "resilience" not in payload["checks"]
