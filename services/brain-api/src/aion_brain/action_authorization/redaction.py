"""Redaction and unsafe-payload detection for dry-run authorization."""

from __future__ import annotations

from typing import Any

REDACTED = "[redacted]"

_SENSITIVE_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}
_RAW_PROMPT_KEY_PARTS = {"raw_prompt", "prompt_text", "system_prompt", "developer_prompt"}
_HIDDEN_REASONING_KEY_PARTS = {
    "chain_of_thought",
    "hidden_reasoning",
    "private_reasoning",
}
_SECRET_VALUE_MARKERS = (
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
)
_RAW_PROMPT_VALUE_MARKERS = (
    "raw prompt",
    "raw_prompt",
    "system prompt:",
    "developer prompt:",
)
_HIDDEN_REASONING_VALUE_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
)


def redact_authorization_payload(
    value: Any,
    *,
    findings: list[dict[str, object]] | None = None,
) -> Any:
    """Return a copy safe for authorization decisions and collect blockers."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            finding = _finding_for_key(normalized)
            if finding is not None:
                if findings is not None:
                    findings.append({"finding": finding, "field": str(key)})
                continue
            redacted[str(key)] = redact_authorization_payload(nested, findings=findings)
        return redacted
    if isinstance(value, list):
        return [redact_authorization_payload(item, findings=findings) for item in value]
    if isinstance(value, str):
        finding = _finding_for_text(value)
        if finding is not None:
            if findings is not None:
                findings.append({"finding": finding})
            return REDACTED
        return value
    return value


def payload_findings(value: Any) -> list[dict[str, object]]:
    """Return unsafe authorization payload findings without exposing the payload."""

    findings: list[dict[str, object]] = []
    redact_authorization_payload(value, findings=findings)
    return findings


def _finding_for_key(normalized: str) -> str | None:
    if any(part in normalized for part in _RAW_PROMPT_KEY_PARTS):
        return "raw_prompt_detected"
    if any(part in normalized for part in _HIDDEN_REASONING_KEY_PARTS):
        return "hidden_reasoning_detected"
    if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
        return "secret_detected"
    return None


def _finding_for_text(value: str) -> str | None:
    lowered = value.lower()
    if any(marker in lowered for marker in _RAW_PROMPT_VALUE_MARKERS):
        return "raw_prompt_detected"
    if any(marker in lowered for marker in _HIDDEN_REASONING_VALUE_MARKERS):
        return "hidden_reasoning_detected"
    if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
        return "secret_detected"
    return None


__all__ = ["REDACTED", "payload_findings", "redact_authorization_payload"]
