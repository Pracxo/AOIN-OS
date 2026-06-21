"""Kernel wiring tests for the temporal scheduler."""

from __future__ import annotations

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_kernel_registers_scheduler_services_and_routes() -> None:
    container = kernel_container()
    names = {record.service_name for record in container.service_registry.list_services()}
    checks = {check.name: check.status for check in container.diagnostics.run()}
    exported = container.contract_export_service.export_contracts(create_app(container))

    assert "scheduler_schedule_service" in names
    assert "scheduler_tick_orchestrator" in names
    assert checks["scheduler_services_present"] == "passed"
    assert checks["scheduler_background_disabled"] == "passed"
    assert "/brain/scheduler/schedules" in exported.openapi["paths"]
    assert "/brain/scheduler/tick" in exported.openapi["paths"]
    assert "SchedulerTickRun" in exported.contracts
