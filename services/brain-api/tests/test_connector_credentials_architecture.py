from __future__ import annotations

from aion_brain.connector_credentials import ConnectorCredentialArchitectureService


def test_connector_credential_boundary_exists_and_blocks_storage() -> None:
    boundary = ConnectorCredentialArchitectureService().boundary()

    assert boundary.credential_storage_enabled is False
    assert boundary.token_storage_enabled is False
    assert boundary.secret_material_present is False
    assert boundary.plaintext_secret_allowed is False
    assert boundary.browser_secret_storage_allowed is False
    assert boundary.log_secret_allowed is False
    assert boundary.external_identity_runtime_enabled is False
    assert boundary.connector_runtime_credential_access_enabled is False
    assert boundary.rotation_required is True
    assert boundary.revocation_required is True
    assert boundary.audit_required is True
    assert boundary.provenance_required is True
