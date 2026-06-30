from __future__ import annotations

from aion_brain.connector_policy.matrix import ConnectorAuthorizationMatrixService


def test_connector_authorization_matrix_never_grants_runtime_paths() -> None:
    entries = ConnectorAuthorizationMatrixService().list_entries()
    dry_run = ConnectorAuthorizationMatrixService().find(
        role="operator",
        action_key="connector_policy.dry_run",
    )
    denied = ConnectorAuthorizationMatrixService().find(
        role="admin",
        action_key="connector.external.call",
    )

    assert dry_run is not None
    assert dry_run.dry_run_allowed is True
    assert denied is not None
    assert denied.decision == "deny"
    assert all(entry.runtime_allowed is False for entry in entries)
    assert all(entry.external_call_allowed is False for entry in entries)
    assert all(entry.credential_access_allowed is False for entry in entries)
    assert all(entry.token_access_allowed is False for entry in entries)
    assert all(entry.activation_allowed is False for entry in entries)

