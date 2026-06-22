"""Module binding redaction tests."""

from aion_brain.module_bindings.redaction import redact_binding_payload


def test_redaction_removes_hidden_reasoning_and_raw_prompt() -> None:
    redacted = redact_binding_payload(
        {
            "safe": "value",
            "hidden_reasoning": "private chain",
            "nested": {"raw_prompt": "secret prompt"},
        }
    )

    assert "hidden_reasoning" not in redacted
    assert "raw_prompt" not in str(redacted)
    assert "private chain" not in str(redacted)
    assert redacted["safe"] == "value"
