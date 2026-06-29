"""Redaction helpers for synthetic connector simulator payloads."""

from __future__ import annotations

from typing import Any

REDACTED = "[redacted]"

_FINDING_KEYS = {
    "api_key": "secret_detected",
    "apikey": "secret_detected",
    "authorization": "secret_detected",
    "bearer": "secret_detected",
    "client_secret": "secret_detected",
    "credential": "credential_field_detected",
    "password": "credential_field_detected",
    "private_key": "secret_detected",
    "secret": "secret_detected",
    "access_token": "token_field_detected",
    "refresh_token": "token_field_detected",
    "id_token": "token_field_detected",
    "token": "token_field_detected",
    "endpoint": "external_url_detected",
    "url": "external_url_detected",
    "uri": "external_url_detected",
    "host": "external_url_detected",
    "dns": "external_url_detected",
    "raw_prompt": "raw_prompt_detected",
    "prompt_text": "raw_prompt_detected",
    "system_prompt": "raw_prompt_detected",
    "developer_prompt": "raw_prompt_detected",
    "chain_of_thought": "hidden_reasoning_detected",
    "hidden_reasoning": "hidden_reasoning_detected",
    "private_reasoning": "hidden_reasoning_detected",
}
_VALUE_FINDINGS = (
    ("http://", "external_url_detected"),
    ("https://", "external_url_detected"),
    ("sk-", "secret_detected"),
    ("xoxb-", "secret_detected"),
    ("ghp_", "secret_detected"),
    ("-----begin private key-----", "secret_detected"),
    ("bearer ", "secret_detected"),
    ("raw prompt", "raw_prompt_detected"),
    ("raw_prompt", "raw_prompt_detected"),
    ("system prompt:", "raw_prompt_detected"),
    ("developer prompt:", "raw_prompt_detected"),
    ("chain-of-thought", "hidden_reasoning_detected"),
    ("chain_of_thought", "hidden_reasoning_detected"),
    ("hidden reasoning", "hidden_reasoning_detected"),
    ("hidden_reasoning", "hidden_reasoning_detected"),
    ("private reasoning", "hidden_reasoning_detected"),
)


def redact_connector_simulator_payload(
    value: Any,
    *,
    findings: list[dict[str, object]] | None = None,
) -> Any:
    """Return a safe copy of a synthetic connector simulator payload."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            finding = _finding_for_key(normalized)
            if finding is not None:
                if findings is not None:
                    findings.append({"finding_type": finding, "field": str(key)})
                continue
            redacted[str(key)] = redact_connector_simulator_payload(
                nested, findings=findings
            )
        return redacted
    if isinstance(value, list):
        return [
            redact_connector_simulator_payload(item, findings=findings)
            for item in value
        ]
    if isinstance(value, str):
        finding = _finding_for_text(value)
        if finding is not None:
            if findings is not None:
                findings.append({"finding_type": finding})
            return REDACTED
        return value
    return value


def payload_findings(value: Any) -> list[dict[str, object]]:
    """Return unsafe simulator payload findings without exposing values."""

    findings: list[dict[str, object]] = []
    redact_connector_simulator_payload(value, findings=findings)
    return findings


def _finding_for_key(normalized: str) -> str | None:
    for part, finding in _FINDING_KEYS.items():
        if part in normalized:
            return finding
    return None


def _finding_for_text(value: str) -> str | None:
    lowered = value.lower()
    for marker, finding in _VALUE_FINDINGS:
        if marker in lowered:
            return finding
    return None


__all__ = ["REDACTED", "payload_findings", "redact_connector_simulator_payload"]
