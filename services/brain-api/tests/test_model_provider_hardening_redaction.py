"""Model provider hardening redaction tests."""

from __future__ import annotations

from aion_brain.model_provider_hardening.redaction import (
    detect_provider_safety_issues,
    redact_provider_payload,
)


def test_provider_redaction_removes_secret_and_prompt_keys() -> None:
    redacted, blocked = redact_provider_payload(
        {"raw_prompt": "do not store", "metadata": {"api_key": "sk-test"}}
    )

    assert blocked == ["raw_prompt", "metadata.api_key"]
    assert "raw_prompt" not in redacted
    assert redacted["redacted_field_1"] == "[REDACTED]"
    assert redacted["metadata"]["redacted_field_2"] == "[REDACTED]"


def test_provider_safety_detects_hidden_reasoning() -> None:
    issues = detect_provider_safety_issues({"notes": "contains hidden reasoning"})

    assert issues[0]["type"] == "hidden_reasoning_detected"
