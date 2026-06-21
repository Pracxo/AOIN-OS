from __future__ import annotations

from aion_brain.grounding.redaction import redact_text, sanitize_payload


def test_redaction_removes_raw_prompt_and_hidden_reasoning() -> None:
    text = redact_text("raw_prompt: keep this\nVisible text sk-secretvalue")
    assert "raw_prompt: keep this" not in text
    assert "sk-secretvalue" not in text

    payload = sanitize_payload({"raw_prompt": "x", "nested": {"token": "secret"}})
    assert payload["raw_prompt"] == "[redacted]"
    assert payload["nested"]["token"] == "[redacted]"
