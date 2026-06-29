from __future__ import annotations

from aion_brain.connector_runtime import ConnectorRuntimeAuditService
from aion_brain.contracts.connector_runtime import ConnectorRuntimeAuditRequest


def test_connector_runtime_audit_passes_disabled_boundaries() -> None:
    result = ConnectorRuntimeAuditService().audit(
        ConnectorRuntimeAuditRequest(owner_scope=["workspace:main"], include_examples=True)
    )

    assert result.status == "passed"
    assert result.runtime_disabled is True
    assert result.external_calls_disabled is True
    assert result.credentials_disabled is True
    assert result.token_storage_disabled is True
    assert result.activation_disabled is True
    assert result.route_registration_disabled is True
    assert result.network_clients_absent is True
    assert result.provider_sdks_absent is True
