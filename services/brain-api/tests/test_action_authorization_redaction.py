from __future__ import annotations

from aion_brain.action_authorization.redaction import (
    REDACTED,
    payload_findings,
    redact_authorization_payload,
)


def test_action_authorization_redacts_unsafe_payload() -> None:
    findings: list[dict[str, object]] = []
    redacted = redact_authorization_payload(
        {
            "summary": "safe",
            "raw_prompt": "system prompt: do not expose",
            "notes": ["hidden reasoning: private"],
        },
        findings=findings,
    )

    assert redacted["summary"] == "safe"
    assert "raw_prompt" not in redacted
    assert redacted["notes"] == [REDACTED]
    assert {item["finding"] for item in findings} == {
        "raw_prompt_detected",
        "hidden_reasoning_detected",
    }


def test_action_authorization_secret_like_payload_has_finding() -> None:
    findings = payload_findings({"api_key": "removed"})

    assert findings == [{"finding": "secret_detected", "field": "api_key"}]
