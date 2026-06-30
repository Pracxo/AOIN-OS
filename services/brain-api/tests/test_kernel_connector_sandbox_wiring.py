from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_connector_sandbox_services() -> None:
    container = kernel_container()

    assert container.connector_sandbox_design_service is not None
    assert container.connector_isolation_boundary_service is not None
    assert container.connector_sandbox_capability_rule_service is not None
    assert container.connector_sandbox_denial_service is not None
    assert container.connector_sandbox_audit_service is not None
    assert container.connector_sandbox_readiness_service is not None
    assert container.connector_sandbox_query_service is not None

    names = {check.name for check in KernelDiagnostics(container).run()}
    assert "connector_sandbox_services_present" in names
    assert "connector_sandbox_runtime_execution_enabled" in names
    assert "connector_sandbox_network_enabled" in names
