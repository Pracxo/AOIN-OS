"""Resilience test runner tests."""

from __future__ import annotations

from aion_brain.contracts.resilience import ResilienceTestRunRequest
from aion_brain.resilience.test_runner import ResilienceTestRunner
from tests.resilience_fakes import (
    SCOPE,
    AllowPolicy,
    FakeTelemetry,
    circuit_breaker,
    dependency_health,
    fault_rule,
    repository,
    retry_policy,
)


def test_resilience_test_runner_reports_failures_and_persists_run() -> None:
    repo = repository()
    telemetry = FakeTelemetry()
    runner = ResilienceTestRunner(
        repo,
        AllowPolicy(),
        dependency_health_service=FakeDependencies(),
        retry_policy_service=FakeRetryPolicies(),
        circuit_breaker_service=FakeBreakers(),
        degraded_mode_service=FakeDegraded(),
        fault_injection_service=FakeFaults(),
        telemetry_service=telemetry,
    )

    run = runner.run(ResilienceTestRunRequest(owner_scope=SCOPE, created_by="tester"))

    assert run.status == "failed"
    assert run.failures
    fetched = runner.get(run.resilience_test_run_id)
    assert fetched is not None
    assert fetched.resilience_test_run_id == run.resilience_test_run_id
    assert fetched.status == run.status
    assert {getattr(event, "event_type", None) for event in telemetry.events} == {
        "resilience_test_started",
        "resilience_test_completed",
    }


class FakeDependencies:
    def check_all(self) -> list[object]:
        return [
            dependency_health("postgres", "unavailable", "critical"),
            dependency_health("optional", "disabled", "optional"),
        ]


class FakeRetryPolicies:
    def list_policies(self) -> list[object]:
        return [retry_policy()]


class FakeBreakers:
    def list_breakers(self) -> list[object]:
        return [circuit_breaker().model_copy(update={"status": "open"})]


class FakeDegraded:
    def list_active(self) -> list[object]:
        return []


class FakeFaults:
    def list_rules(self, status: str | None = None) -> list[object]:
        return [fault_rule()] if status == "active" else []
