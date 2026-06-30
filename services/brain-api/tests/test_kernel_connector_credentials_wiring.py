from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_connector_credential_services() -> None:
    container = kernel_container()

    assert container.connector_credential_architecture_service is not None
    assert container.connector_credential_lifecycle_service is not None
    assert container.connector_credential_authorization_service is not None
    assert container.connector_credential_denial_service is not None
    assert container.connector_credential_audit_service is not None
    assert container.connector_credential_readiness_service is not None
    assert container.connector_secret_redaction_service is not None
    assert container.connector_credential_query_service is not None

    names = {check.name for check in KernelDiagnostics(container).run()}
    assert "connector_credential_services_present" in names
    assert "connector_credentials_storage_enabled" in names
    assert "connector_runtime_credential_access_enabled" in names
