from __future__ import annotations

from aion_brain.local_auth.redaction import (
    REDACTED,
    local_auth_payload_has_unsafe_content,
    scrub_local_auth_payload,
)


def test_local_auth_redaction_removes_unsafe_keys_and_values() -> None:
    findings: list[dict[str, object]] = []

    result = scrub_local_auth_payload(
        {
            "safe": "visible",
            "raw_prompt": "do not expose",
            "nested": {"summary": "hidden reasoning should be private"},
        },
        findings=findings,
    )

    assert result == {"safe": "visible", "nested": {"summary": REDACTED}}
    assert findings


def test_local_auth_payload_detection_finds_secret_like_content() -> None:
    assert local_auth_payload_has_unsafe_content({"items": [{"private_key": "value"}]})
    assert not local_auth_payload_has_unsafe_content({"items": [{"safe": "value"}]})
