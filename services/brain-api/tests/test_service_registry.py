"""Kernel service registry tests."""

from aion_brain.kernel.service_registry import KernelServiceRegistry
from tests.kernel_fakes import FakeTelemetry


def test_registry_registers_lists_and_updates_health() -> None:
    telemetry = FakeTelemetry()
    registry = KernelServiceRegistry(telemetry_service=telemetry)
    record = registry.register_service("example", "service", "local")
    assert registry.list_services() == [record]
    updated = registry.update_health("example", {"ready": True}, "healthy")
    assert updated.status == "healthy"
    assert registry.list_services(service_type="service") == [updated]
    assert telemetry.events
