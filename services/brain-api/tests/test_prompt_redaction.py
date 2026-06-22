from __future__ import annotations

from aion_brain.prompts.redaction import (
    contains_secret_like_text,
    redact_prompt_text,
    sanitize_prompt_payload,
)


def test_prompt_redaction_removes_secret_values() -> None:
    redacted, metadata = redact_prompt_text("token sk-1234567890abcdef")

    assert "[redacted]" in redacted
    assert metadata["sensitive_value_count"] == 1


def test_prompt_payload_sanitizer_redacts_secret_keys() -> None:
    assert sanitize_prompt_payload({"api_key": "value"}) == {"api_key": "[redacted]"}
    assert contains_secret_like_text("password: value") is True
