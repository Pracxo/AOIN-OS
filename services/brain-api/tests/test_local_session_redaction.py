from __future__ import annotations

from aion_brain.local_session.redaction import (
    REDACTED,
    local_session_payload_has_unsafe_content,
    scrub_local_session_payload,
)


def test_local_session_redaction_removes_secret_like_keys_and_text() -> None:
    payload = {
        "safe": "visible",
        "password": "removed",
        "nested": {"value": "sk-test"},
        "token_issued": False,
    }
    findings: list[dict[str, object]] = []

    scrubbed = scrub_local_session_payload(payload, findings=findings)

    assert "password" not in scrubbed
    assert scrubbed["nested"]["value"] == REDACTED
    assert scrubbed["token_issued"] is False
    assert findings
    assert local_session_payload_has_unsafe_content(payload) is True
