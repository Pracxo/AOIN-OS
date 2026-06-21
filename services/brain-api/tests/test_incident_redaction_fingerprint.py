from __future__ import annotations

from aion_brain.incidents.fingerprint import build_correlation_key, build_signal_fingerprint
from aion_brain.incidents.redaction import redact_incident_payload


def test_incident_redaction_removes_raw_prompt_and_secrets() -> None:
    payload = {
        "raw_prompt": "system prompt: secret",
        "nested": {"api_key": "sk-secret", "safe": "ok"},
    }

    redacted = redact_incident_payload(payload)

    assert redacted["raw_prompt"] == "[redacted]"
    assert redacted["nested"]["api_key"] == "[redacted]"
    assert redacted["nested"]["safe"] == "ok"


def test_incident_fingerprint_is_deterministic() -> None:
    first = build_signal_fingerprint("alert", "alert-1", "failed", "A thing failed.")
    second = build_signal_fingerprint("alert", "alert-1", "failed", "A thing failed.")

    assert first == second
    assert len(first) == 64


def test_incident_correlation_key_is_deterministic() -> None:
    first = build_correlation_key("alert", "failed", "trace-1", "target-1")
    second = build_correlation_key("alert", "failed", "trace-1", "target-1")

    assert first == second
    assert first == "incident:alert:failed:trace-1:target-1"
