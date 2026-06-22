"""Kernel boot tests."""

from aion_brain.kernel.boot import KernelBootService
from tests.kernel_fakes import kernel_container


def test_boot_service_creates_ready_record() -> None:
    container = kernel_container()
    record = container.boot_service.boot()
    assert record.status == "ready"
    assert container.boot_service.get_latest_boot() == record


def test_boot_service_marks_noncritical_failure_degraded() -> None:
    container = kernel_container()
    checks = container.diagnostics.run()
    checks[1] = checks[1].model_copy(update={"status": "warning"})
    container.diagnostics.run = lambda: checks  # type: ignore[method-assign]
    service = KernelBootService(
        container=container,
        repository=container.kernel_repository,
        registry=container.service_registry,
        diagnostics=container.diagnostics,
    )
    assert service.boot().status == "degraded"
