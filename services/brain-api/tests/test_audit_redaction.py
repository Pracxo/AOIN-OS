"""Audit redaction tests."""

from __future__ import annotations

from aion_brain.audit_integrity.redaction import redact_audit_payload


def test_redaction_removes_raw_prompt() -> None:
    payload, metadata = redact_audit_payload({"raw_prompt": "do not store"})

    assert payload["raw_prompt"] == "[REDACTED]"
    assert metadata["redaction_count"] == 1


def test_redaction_removes_hidden_reasoning() -> None:
    payload, metadata = redact_audit_payload({"hidden_reasoning": "private", "ok": True})

    assert payload == {"ok": True}
    assert metadata["removed_count"] == 1
