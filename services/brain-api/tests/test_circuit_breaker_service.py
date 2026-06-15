"""Circuit breaker service tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aion_brain.resilience.circuit_breakers import CircuitBreakerService
from tests.resilience_fakes import AllowPolicy, FakeTelemetry, circuit_breaker, repository


def test_circuit_breaker_opens_half_opens_and_closes() -> None:
    telemetry = FakeTelemetry()
    service = CircuitBreakerService(repository(), AllowPolicy(), telemetry_service=telemetry)
    service.create_breaker(circuit_breaker())

    first = service.record_failure("command", "first")
    second = service.record_failure("command", "second")

    assert first.status == "closed"
    assert second.status == "open"
    assert service.allow_call("command") is False
    assert service.allow_call("command", datetime.now(UTC) + timedelta(seconds=2)) is True
    assert service.record_success("command").status == "closed"
    assert {getattr(event, "event_type", None) for event in telemetry.events} >= {
        "circuit_breaker_opened",
        "circuit_breaker_half_opened",
        "circuit_breaker_closed",
    }


def test_circuit_breaker_reset_closes_breaker() -> None:
    service = CircuitBreakerService(repository(), AllowPolicy())
    service.create_breaker(circuit_breaker())
    service.record_failure("command")
    opened = service.record_failure("command")

    reset = service.reset(opened.name, "tester", "manual reset")

    assert reset.status == "closed"
    assert reset.failure_count == 0
    assert reset.metadata["reset_reason"] == "manual reset"
