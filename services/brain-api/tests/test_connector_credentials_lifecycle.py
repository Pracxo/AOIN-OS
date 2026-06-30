from __future__ import annotations

from aion_brain.connector_credentials import ConnectorCredentialLifecycleService


def test_connector_credential_lifecycle_storage_states_are_future_only() -> None:
    states = ConnectorCredentialLifecycleService().list_states()

    assert {state.state_key for state in states} >= {
        "requested",
        "approved_for_future_storage",
        "provisioned_future",
        "rotated_future",
        "revoked_future",
        "expired_future",
        "quarantined_future",
        "deleted_future",
    }
    for state in states:
        if state.requires_secret_store:
            assert state.allowed_today is False
            assert state.future_only is True
        assert state.requires_audit is True
        assert state.requires_provenance is True
