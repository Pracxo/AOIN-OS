from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_connector_runtime_services() -> None:
    container = kernel_container()

    assert container.connector_runtime_gate_service is not None
    assert container.mock_connector_manifest_service is not None
    assert container.connector_egress_preview_service is not None
    assert container.connector_ingress_preview_service is not None
    assert container.connector_runtime_audit_service is not None
    assert container.connector_runtime_query_service is not None

    names = {check.name for check in KernelDiagnostics(container).run()}
    assert "connector_runtime_services_present" in names
    assert "connector_external_calls_enabled" in names
    assert "connector_token_storage_enabled" in names
