"""Prompt redaction tests."""

from aion_brain.model_gateway.redaction import PromptRedactor
from tests.model_gateway_fakes import prompt


def test_prompt_redactor_detects_api_key_like_text() -> None:
    record = PromptRedactor().inspect(prompt("api_key=secret-value-123456"))
    assert "api_key_like" in record.redaction_types


def test_prompt_redactor_detects_bearer_token_like_text() -> None:
    record = PromptRedactor().inspect(prompt("Bearer abcdefghijklmnopqrstuvwxyz"))
    assert "bearer_token_like" in record.redaction_types


def test_prompt_redactor_blocks_when_configured() -> None:
    _, record = PromptRedactor(block_on_secret=True).redact(prompt("password=secret123"))
    assert record.blocked is True
    assert record.reason == "secret_like_content_detected"


def test_prompt_redactor_redacts_when_not_blocking() -> None:
    redacted, record = PromptRedactor(block_on_secret=False).redact(prompt("password=secret123"))
    assert record.blocked is False
    assert "[REDACTED]" in redacted.goal
