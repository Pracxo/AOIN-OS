"""Module mock runtime redaction tests."""

from __future__ import annotations

from aion_brain.module_mock_runtime.redaction import redact_module_mock_payload


def test_redaction_removes_raw_prompt_hidden_reasoning_and_executable_fields() -> None:
    redacted = redact_module_mock_payload(
        {
            "raw_prompt": "do not store",
            "hidden_reasoning": "private reasoning",
            "nested": {"script": "print(1)", "safe": "value"},
            "api_key": "sk-test",
        }
    )

    assert redacted["raw_prompt"] == "[redacted]"
    assert redacted["hidden_reasoning"] == "[redacted]"
    assert redacted["nested"]["script"] == "[redacted]"
    assert redacted["nested"]["safe"] == "value"
    assert redacted["api_key"] == "[redacted]"
