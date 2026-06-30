from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.connector_credentials import (
    ConnectorCredentialAuthorizationEntry,
    ConnectorCredentialBoundary,
    ConnectorCredentialLifecycleState,
    ConnectorCredentialReadinessRequest,
    ConnectorCredentialReadinessResult,
    ConnectorSecretRedactionResult,
    utc_now,
)


def test_connector_credential_boundary_rejects_storage_and_material() -> None:
    boundary = ConnectorCredentialBoundary(
        credential_boundary_id="connector-credential-boundary-test",
        name="Connector Credential Boundary",
        description="Design-only credential boundary.",
        credential_storage_enabled=False,
        token_storage_enabled=False,
        secret_material_present=False,
        plaintext_secret_allowed=False,
        browser_secret_storage_allowed=False,
        log_secret_allowed=False,
        external_identity_runtime_enabled=False,
        connector_runtime_credential_access_enabled=False,
        rotation_required=True,
        revocation_required=True,
        audit_required=True,
        provenance_required=True,
        created_at=utc_now(),
    )

    assert boundary.credential_storage_enabled is False
    assert boundary.token_storage_enabled is False
    assert boundary.secret_material_present is False

    with pytest.raises(ValidationError):
        ConnectorCredentialBoundary(
            **boundary.model_copy(update={"credential_storage_enabled": True}).model_dump()
        )
    with pytest.raises(ValidationError):
        ConnectorCredentialBoundary(
            **boundary.model_copy(update={"external_identity_runtime_enabled": True}).model_dump()
        )


def test_connector_credential_lifecycle_storage_states_are_future_only() -> None:
    state = ConnectorCredentialLifecycleState(
        state_key="provisioned_future",
        title="Provisioned Future",
        description="Future storage state.",
        allowed_today=False,
        future_only=True,
        requires_production_auth=True,
        requires_secret_store=True,
        requires_rotation_plan=True,
        requires_revocation_plan=True,
        requires_audit=True,
        requires_provenance=True,
    )

    assert state.future_only is True
    assert state.allowed_today is False

    with pytest.raises(ValidationError):
        ConnectorCredentialLifecycleState(
            **state.model_copy(update={"allowed_today": True}).model_dump()
        )


def test_connector_credential_authorization_never_allows_material_access() -> None:
    entry = ConnectorCredentialAuthorizationEntry(
        role="operator",
        action_key="connector_credentials.readiness.preview",
        decision="allow_preview",
        credential_access_allowed=False,
        token_access_allowed=False,
        secret_material_allowed=False,
        storage_allowed=False,
        rotation_allowed=False,
        revocation_allowed=False,
        audit_required=True,
        review_required=True,
        reason="preview_only",
    )

    assert entry.credential_access_allowed is False
    assert entry.token_access_allowed is False

    with pytest.raises(ValidationError):
        ConnectorCredentialAuthorizationEntry(
            **entry.model_copy(update={"token_access_allowed": True}).model_dump()
        )


def test_connector_credential_request_rejects_unsafe_metadata() -> None:
    request = ConnectorCredentialReadinessRequest(
        connector_key="mock.local.preview",
        owner_scope=["workspace:main"],
        requested_scopes=["connector_credentials.readiness.preview"],
    )

    assert request.connector_key == "mock.local.preview"

    with pytest.raises(ValidationError):
        ConnectorCredentialReadinessRequest(
            connector_key="Mock.Local",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        ConnectorCredentialReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            metadata={"external_url": "blocked"},
        )


def test_connector_credential_readiness_result_keeps_storage_disabled() -> None:
    result = ConnectorCredentialReadinessResult(
        connector_credential_readiness_id="connector-credential-readiness-test",
        connector_key="mock.local.preview",
        status="blocked",
        credential_ready=False,
        credential_storage_allowed=False,
        token_storage_allowed=False,
        credential_access_allowed=False,
        token_access_allowed=False,
        secret_material_present=False,
        external_identity_runtime_allowed=False,
        rotation_required=True,
        revocation_required=True,
        audit_required=True,
        provenance_required=True,
        created_at=utc_now(),
    )

    assert result.credential_storage_allowed is False
    assert result.token_storage_allowed is False

    with pytest.raises(ValidationError):
        ConnectorCredentialReadinessResult(
            **result.model_copy(update={"secret_material_present": True}).model_dump()
        )


def test_connector_secret_redaction_result_allows_redacted_payload_only() -> None:
    result = ConnectorSecretRedactionResult(
        redaction_id="connector-secret-redaction-test",
        status="redacted",
        redaction_applied=True,
        secret_detected=True,
        token_detected=True,
        credential_field_detected=True,
        redacted_payload={"client_secret": "[REDACTED]"},
        blocked_fields=["client_secret"],
        metadata={"storage_allowed": False},
        created_at=utc_now(),
    )

    assert result.redaction_applied is True
    assert result.redacted_payload["client_secret"] == "[REDACTED]"
