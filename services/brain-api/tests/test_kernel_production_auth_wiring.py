from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_production_auth_core_without_routes() -> None:
    container = kernel_container()

    assert container.production_auth_core_config is not None
    assert container.production_auth_core_service is not None
    status = container.production_auth_core_service.status()
    assert status.production_auth_core_state == "implemented_disabled"
    assert status.runtime_enabled is False


def test_kernel_diagnostics_include_production_auth_core_redacted_snapshot() -> None:
    container = kernel_container()
    names = {check.name for check in KernelDiagnostics(container).run()}

    assert "production_auth_core_implemented" in names
    assert "production_auth_core_runtime_disabled" in names
    assert "production_auth_core_guard_hold_active" in names
    assert "production_auth_core_diagnostics_redacted" in names
