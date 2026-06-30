from __future__ import annotations

from aion_brain.connector_credentials import ConnectorSecretRedactionService


def test_connector_secret_redaction_detects_and_redacts_secret_like_fields() -> None:
    result = ConnectorSecretRedactionService().preview(
        {
            "client_secret": "placeholder",
            "access_token": "placeholder",
            "nested": {"credential_hint": "placeholder"},
            "safe": "visible",
        }
    )

    assert result.redaction_applied is True
    assert result.secret_detected is True
    assert result.token_detected is True
    assert result.credential_field_detected is True
    assert result.redacted_payload["client_secret"] == "[REDACTED]"
    assert result.redacted_payload["access_token"] == "[REDACTED]"
    assert result.redacted_payload["nested"]["credential_hint"] == "[REDACTED]"
    assert result.redacted_payload["safe"] == "visible"
