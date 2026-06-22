from __future__ import annotations

from aion_brain.dialogue.redaction import redact_message_content


def test_dialogue_redaction_redacts_secret_like_content() -> None:
    content, redacted = redact_message_content("api_key=sk-test-secret\nhello")

    assert redacted is True
    assert "sk-test-secret" not in content
    assert "[REDACTED]" in content


def test_dialogue_redaction_drops_hidden_reasoning_markers() -> None:
    content, redacted = redact_message_content("chain_of_thought: hide this\nvisible")

    assert redacted is True
    assert "chain_of_thought" not in content
    assert "visible" in content
