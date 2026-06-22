"""Release candidate redaction tests."""

from __future__ import annotations

from aion_brain.release_candidate.redaction import redact_rc_payload, safe_rc_summary


def test_redaction_removes_hidden_reasoning_and_secret_values() -> None:
    payload = {
        "status": "passed",
        "api_key": "sk-test",
        "nested": {"raw_prompt": "do not keep", "message": "ok"},
    }

    redacted = redact_rc_payload(payload)

    assert "api_key" not in redacted
    assert "raw_prompt" not in redacted["nested"]
    assert redacted["nested"]["message"] == "ok"


def test_safe_summary_is_json_compatible() -> None:
    summary = safe_rc_summary({"value": object()})

    assert isinstance(summary["value"], str)
