from __future__ import annotations

from aion_brain.operator_console.redaction import (
    REDACTED,
    payload_has_sensitive_content,
    redact_console_payload,
)


def test_redaction_removes_source_prompt_and_private_reasoning() -> None:
    payload = {
        "safe": "keep",
        "raw_prompt": "remove this",
        "nested": {"hidden_reasoning": "remove this too"},
    }

    redacted = redact_console_payload(payload)

    assert redacted["safe"] == "keep"
    assert redacted["raw_prompt"] == REDACTED
    assert redacted["nested"]["hidden_reasoning"] == REDACTED
    assert payload_has_sensitive_content(payload) is True
    assert payload_has_sensitive_content(redacted) is True
