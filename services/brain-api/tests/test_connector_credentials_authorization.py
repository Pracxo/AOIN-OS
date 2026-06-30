from __future__ import annotations

from aion_brain.connector_credentials import ConnectorCredentialAuthorizationService


def test_connector_credential_authorization_denies_material_access() -> None:
    entries = ConnectorCredentialAuthorizationService().list_entries()

    assert any(
        entry.action_key == "connector_credentials.readiness.preview" for entry in entries
    )
    assert all(entry.credential_access_allowed is False for entry in entries)
    assert all(entry.token_access_allowed is False for entry in entries)
    assert all(entry.secret_material_allowed is False for entry in entries)
    assert all(entry.storage_allowed is False for entry in entries)
    assert all(entry.audit_required is True for entry in entries)
