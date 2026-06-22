"""Degraded mode service tests."""

from __future__ import annotations

from aion_brain.resilience.degraded_mode import DegradedModeService
from tests.resilience_fakes import dependency_health, repository


def test_degraded_mode_enter_is_idempotent_and_resolves() -> None:
    service = DegradedModeService(repository())

    first = service.enter("memory", "medium", "adapter unavailable", ["adapter"], ["fallback"], [])
    second = service.enter("memory", "medium", "adapter unavailable", ["adapter"], ["fallback"], [])
    resolved = service.resolve(first.degraded_event_id, "tester", "restored")

    assert first.degraded_event_id == second.degraded_event_id
    assert resolved.status == "resolved"
    assert service.list_active() == []


def test_degraded_status_reports_unhealthy_for_critical_dependency() -> None:
    class FakeDependencyHealth:
        def list_latest(self) -> list[object]:
            return [dependency_health("postgres", "unavailable", "critical")]

    service = DegradedModeService(repository(), dependency_health_service=FakeDependencyHealth())

    assert service.status().overall_status == "unhealthy"
