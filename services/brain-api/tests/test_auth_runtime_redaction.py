from __future__ import annotations

from aion_brain.auth_runtime.redaction import (
    REDACTED,
    auth_runtime_payload_has_unsafe_content,
    payload_findings,
    redact_auth_runtime_payload,
)


def test_auth_runtime_redaction_blocks_auth_material_keys() -> None:
    payload = {"token_value": "not-used", "safe_claim": "operator"}

    redacted = redact_auth_runtime_payload(payload)
    findings = payload_findings(payload)

    assert redacted == {"safe_claim": "operator"}
    assert findings == [{"finding": "secret_detected", "field": "token_value"}]
    assert auth_runtime_payload_has_unsafe_content(payload) is True


def test_auth_runtime_redaction_blocks_secret_like_values() -> None:
    redacted = redact_auth_runtime_payload({"claim": "sk-example"})

    assert redacted == {"claim": REDACTED}
    assert payload_findings({"claim": "sk-example"}) == [{"finding": "secret_detected"}]
