from __future__ import annotations

from aion_brain.connector_simulator.redaction import (
    REDACTED,
    payload_findings,
    redact_connector_simulator_payload,
)


def test_connector_simulator_redaction_removes_unsafe_fields() -> None:
    findings: list[dict[str, object]] = []
    payload = {
        "safe": "value",
        "api_key": "placeholder",
        "nested": {"hidden_reasoning": "not allowed"},
    }

    redacted = redact_connector_simulator_payload(payload, findings=findings)

    assert redacted == {"safe": "value", "nested": {}}
    assert {item["finding_type"] for item in findings} == {
        "secret_detected",
        "hidden_reasoning_detected",
    }


def test_connector_simulator_redaction_masks_unsafe_values() -> None:
    payload = {"items": ["safe", "raw prompt material"]}

    assert redact_connector_simulator_payload(payload)["items"] == ["safe", REDACTED]
    assert payload_findings(payload)[0]["finding_type"] == "raw_prompt_detected"
