from __future__ import annotations

from aion_brain.explanations.redaction import (
    contains_hidden_reasoning_marker,
    contains_raw_prompt_marker,
    redact_explanation_text,
    sanitize_explanation_payload,
)
from aion_brain.explanations.templates import explanation_template


def test_redaction_removes_secret_values_and_raw_prompt_keys() -> None:
    text, metadata = redact_explanation_text("token sk-abc123 was present")
    payload, payload_metadata = sanitize_explanation_payload(
        {"safe": "ok", "raw_prompt": "hidden", "nested": {"api_key": "sk-test"}}
    )

    assert "[redacted_secret]" in text
    assert metadata["redacted"] is True
    assert "raw_prompt" not in payload
    assert payload_metadata["removed_count"] == 2


def test_marker_helpers_delegate_without_recursion() -> None:
    assert contains_hidden_reasoning_marker("chain of thought") is True
    assert contains_raw_prompt_marker("system prompt") is True


def test_templates_are_generic() -> None:
    assert explanation_template("missing") == explanation_template("generic")
    assert "policy" in explanation_template("policy_blocked")
