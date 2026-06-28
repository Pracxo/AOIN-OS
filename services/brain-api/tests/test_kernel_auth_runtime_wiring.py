from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_auth_runtime_services() -> None:
    container = kernel_container()

    assert container.auth_runtime_gate_service is not None
    assert container.mock_claims_preview_service is not None
    assert container.auth_runtime_audit_service is not None
    assert container.auth_runtime_query_service is not None

    names = {check.name for check in KernelDiagnostics(container).run()}
    assert "auth_runtime_services_present" in names
    assert "auth_runtime_token_issuance_enabled" in names
