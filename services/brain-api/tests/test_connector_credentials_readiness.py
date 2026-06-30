from __future__ import annotations

from aion_brain.connector_credentials import (
    ConnectorCredentialArchitectureService,
    ConnectorCredentialAuthorizationService,
    ConnectorCredentialDenialService,
    ConnectorCredentialReadinessService,
)
from aion_brain.contracts.connector_credentials import ConnectorCredentialReadinessRequest


def _service() -> ConnectorCredentialReadinessService:
    return ConnectorCredentialReadinessService(
        architecture_service=ConnectorCredentialArchitectureService(),
        authorization_service=ConnectorCredentialAuthorizationService(),
        denial_service=ConnectorCredentialDenialService(),
    )


def test_connector_credential_readiness_blocks_storage_paths() -> None:
    result = _service().evaluate(
        ConnectorCredentialReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            requested_scopes=["connector_credentials.readiness.preview"],
        )
    )

    assert result.status == "blocked"
    assert result.credential_ready is False
    assert result.credential_storage_allowed is False
    assert result.token_storage_allowed is False
    assert result.credential_access_allowed is False
    assert result.token_access_allowed is False
    assert result.secret_material_present is False
    assert result.external_identity_runtime_allowed is False


def test_connector_credential_readiness_explicit_denial_is_reported() -> None:
    result = _service().evaluate(
        ConnectorCredentialReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            requested_scopes=["connector.credentials.store"],
        )
    )

    assert result.status == "blocked"
    assert any(item["blocker_key"] == "explicit_credential_denial_rule" for item in result.blockers)
