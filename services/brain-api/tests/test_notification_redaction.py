"""Notification redaction tests."""

from __future__ import annotations

from aion_brain.notifications.redaction import redact_payload, redact_text


def test_redact_text_hides_secret_and_raw_prompt_markers() -> None:
    assert redact_text("the token is sk-test") == "[redacted secret-like value]"
    assert redact_text("raw prompt: hidden") == "[redacted hidden reasoning or raw prompt]"


def test_redact_payload_redacts_secret_like_keys_recursively() -> None:
    payload = {
        "safe": "value",
        "api_key": "sk-test",
        "nested": [{"raw_prompt": "private"}],
    }

    redacted = redact_payload(payload)

    assert redacted == {
        "safe": "value",
        "redacted_field_2": "[redacted]",
        "nested": [{"redacted_field_1": "[redacted]"}],
    }
