from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_connector_policy_services() -> None:
    container = kernel_container()

    assert container.connector_policy_catalog_service is not None
    assert container.connector_authorization_matrix_service is not None
    assert container.connector_policy_dry_run_service is not None
    assert container.connector_policy_traceability_service is not None
    assert container.connector_policy_query_service is not None

    names = {check.name for check in KernelDiagnostics(container).run()}
    assert "connector_policy_services_present" in names
    assert "connector_policy_runtime_allow_enabled" in names
    assert "connector_policy_external_calls_enabled" in names

