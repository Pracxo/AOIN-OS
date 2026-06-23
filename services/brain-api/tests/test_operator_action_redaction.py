from __future__ import annotations

from aion_brain.operator_actions.redaction import redact_operator_action_payload


def test_operator_action_redaction_removes_protected_prompt_and_reasoning() -> None:
    redacted, findings = redact_operator_action_payload(
        {
            "raw_prompt": "do not store",
            "notes": "hidden reasoning: private trace",
            "nested": {"api_key": "sk-testsecret"},
        }
    )

    serialized = str(redacted).lower()
    assert "raw_prompt" not in serialized
    assert "hidden reasoning" not in serialized
    assert "api_key" not in serialized
    assert findings
