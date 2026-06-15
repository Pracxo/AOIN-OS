"""Dependency health service tests."""

from __future__ import annotations

from aion_brain.resilience.dependency_health import DependencyHealthService
from tests.resilience_fakes import FakeTelemetry, repository, settings


def test_dependency_health_records_success_failure_and_exceptions() -> None:
    telemetry = FakeTelemetry()
    service = DependencyHealthService(
        repository(),
        settings=settings(),
        telemetry_service=telemetry,
        checkers={
            "ok": lambda: True,
            "down": lambda: False,
            "raises": _raise,
        },
    )

    records = service.check_all()

    statuses = {record.dependency_name: record.status for record in records}
    assert statuses == {"ok": "healthy", "down": "unavailable", "raises": "unavailable"}
    assert len(telemetry.events) == 3


def test_dependency_health_list_latest_filters_by_type_and_component() -> None:
    service = DependencyHealthService(
        repository(),
        settings=settings(),
        checkers={"ok": lambda: True, "down": lambda: False},
    )
    service.check_all()

    assert [record.dependency_name for record in service.list_latest(component="ok")] == ["ok"]
    assert len(service.list_latest(dependency_type="optional_adapter")) == 2


def _raise() -> bool:
    raise RuntimeError("unavailable")
