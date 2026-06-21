"""Contract Registry redaction tests."""

from __future__ import annotations

from aion_brain.contract_registry.redaction import redact_contract_payload


def test_contract_redaction_removes_raw_prompt_and_hidden_reasoning() -> None:
    payload = {
        "properties": {"raw_prompt": {"type": "string"}},
        "required": ["raw_prompt", "token"],
        "description": "hidden reasoning should not be stored",
    }

    redacted = redact_contract_payload(payload)

    assert "raw_prompt" not in str(redacted)
    assert "hidden reasoning" not in str(redacted)
    assert "token" not in str(redacted)
    assert "[redacted]" in str(redacted)
