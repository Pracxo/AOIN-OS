from __future__ import annotations

from aion_brain.connector_credentials.denials import ConnectorCredentialDenialService


def test_connector_credential_denials_cover_future_material_actions() -> None:
    service = ConnectorCredentialDenialService()

    assert service.denial_for("connector.credentials.store") is not None
    assert service.denial_for("connector.tokens.read") is not None
    assert service.denial_for("connector.oauth.exchange") is not None
    assert service.denial_for("connector_credentials.readiness.preview") is None
    assert all(
        service.denial_for(action)["credential_storage_allowed"] is False
        for action in service.denied_actions()
        if service.denial_for(action) is not None
    )
