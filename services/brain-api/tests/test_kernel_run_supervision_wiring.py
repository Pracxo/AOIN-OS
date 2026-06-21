from __future__ import annotations

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_kernel_registers_run_supervision_services_and_routes() -> None:
    container = kernel_container()
    names = {record.service_name for record in container.service_registry.list_services()}
    checks = {check.name: check.status for check in container.diagnostics.run()}
    exported = container.contract_export_service.export_contracts(create_app(container))

    assert "run_supervision_service" in names
    assert "run_status_sampler" in names
    assert checks["run_supervision_enabled"] == "passed"
    assert checks["run_supervision_background_enabled"] == "passed"
    assert checks["compensation_execution_enabled"] == "passed"
    assert "/brain/run-supervision/runs" in exported.openapi["paths"]
    assert "RunSupervisionRecord" in exported.contracts
