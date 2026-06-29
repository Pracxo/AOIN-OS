from __future__ import annotations

from aion_brain.connector_runtime.redaction import (
    connector_runtime_payload_has_unsafe_content,
    redact_connector_runtime_payload,
)


def test_connector_runtime_redaction_blocks_sensitive_keys() -> None:
    payload = {"safe": "value", "credential": "local-preview"}
    redacted = redact_connector_runtime_payload(payload)

    assert redacted["safe"] == "value"
    assert "credential" not in redacted
    assert connector_runtime_payload_has_unsafe_content(payload) is True


def test_connector_runtime_redaction_blocks_hidden_reasoning() -> None:
    payload = {"notes": "hidden_reasoning should not pass"}
    redacted = redact_connector_runtime_payload(payload)

    assert redacted["notes"] == "[redacted]"
    assert connector_runtime_payload_has_unsafe_content(payload) is True
