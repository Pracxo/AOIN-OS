"""Resilience API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.api.resilience import get_dependency_health_service, get_resilience_test_runner
from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container
from tests.resilience_fakes import (
    SCOPE,
    circuit_breaker,
    dependency_health,
    fault_rule,
    retry_policy,
)
from tests.resilience_fakes import (
    test_run as resilience_test_run,
)


def test_resilience_status_and_dependency_check_apis_work() -> None:
    app = create_app(kernel_container())
    app.dependency_overrides[get_dependency_health_service] = lambda: FakeDependencyHealth()
    client = TestClient(app)

    status = client.get("/brain/resilience/status", params={"scope": SCOPE})
    dependencies = client.post("/brain/resilience/dependencies/check", json={"scope": SCOPE})

    assert status.status_code == 200
    assert status.json()["overall_status"] == "healthy"
    assert dependencies.status_code == 200
    assert dependencies.json()[0]["dependency_name"] == "postgres"


def test_retry_policy_and_circuit_breaker_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))

    retry = client.post(
        "/brain/resilience/retry-policies",
        json=retry_policy().model_dump(mode="json"),
    )
    retry_list = client.get("/brain/resilience/retry-policies", params={"target_type": "command"})
    seeded = client.post("/brain/resilience/retry-policies/seed-defaults", json={"dry_run": True})
    breaker = client.post(
        "/brain/resilience/circuit-breakers",
        json=circuit_breaker().model_dump(mode="json"),
    )
    breaker_list = client.get("/brain/resilience/circuit-breakers")
    reset = client.post(
        "/brain/resilience/circuit-breakers/command/reset",
        json={"reason": "api reset"},
    )

    assert retry.status_code == 200
    assert retry_list.status_code == 200
    assert seeded.json()["policy_count"] >= 1
    assert breaker.status_code == 200
    assert breaker_list.status_code == 200
    assert reset.status_code == 200
    assert reset.json()["status"] == "closed"


def test_degraded_fault_rule_and_resilience_test_apis_work() -> None:
    container = kernel_container()
    container.degraded_mode_service.enter(
        "semantic_memory",
        "medium",
        "adapter unavailable",
        ["adapter"],
        ["local_baseline"],
        [],
    )
    app = create_app(container)
    app.dependency_overrides[get_resilience_test_runner] = lambda: FakeResilienceRunner()
    client = TestClient(app)

    degraded = client.get("/brain/resilience/degraded")
    fault = client.post("/brain/resilience/fault-rules", json=fault_rule().model_dump(mode="json"))
    fault_list = client.get("/brain/resilience/fault-rules", params={"status": "active"})
    disabled = client.post(
        "/brain/resilience/fault-rules/fault-command/disable",
        json={"reason": "api disable"},
    )
    run = client.post("/brain/resilience/test/run", json={"owner_scope": SCOPE})
    fetched = client.get(f"/brain/resilience/test-runs/{run.json()['resilience_test_run_id']}")

    assert degraded.status_code == 200
    assert degraded.json()[0]["component"] == "semantic_memory"
    assert fault.status_code == 200
    assert fault_list.status_code == 200
    assert disabled.status_code == 200
    assert run.status_code == 200
    assert fetched.status_code == 200


class FakeDependencyHealth:
    def check_all(self) -> list[object]:
        return [dependency_health("postgres")]

    def list_latest(self, **_kwargs: object) -> list[object]:
        return [dependency_health("postgres")]


class FakeResilienceRunner:
    def __init__(self) -> None:
        self.run_record = resilience_test_run()

    def run(self, request: object) -> object:
        return self.run_record

    def get(self, resilience_test_run_id: str) -> object | None:
        if resilience_test_run_id == self.run_record.resilience_test_run_id:
            return self.run_record
        return None
