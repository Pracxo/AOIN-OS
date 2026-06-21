"""Redaction helpers for incident-owned records."""

from __future__ import annotations

from typing import Any

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
_TEXT_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
    "raw prompt",
    "raw_prompt",
    "system prompt:",
    "developer prompt:",
    "sk-",
    "ghp_",
    "xoxb-",
    "-----begin private key-----",
)


def redact_incident_text(value: str) -> str:
    """Remove hidden reasoning, raw prompt markers, and obvious secret values."""

    lowered = value.lower()
    if any(marker in lowered for marker in _TEXT_MARKERS):
        return "[redacted incident-sensitive content]"
    return value


def redact_incident_payload(value: Any) -> Any:
    """Recursively redact incident payloads without retaining removed values."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                redacted[str(key)] = "[redacted]"
            else:
                redacted[str(key)] = redact_incident_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_incident_payload(item) for item in value]
    if isinstance(value, str):
        return redact_incident_text(value)
    return value


__all__ = ["redact_incident_payload", "redact_incident_text"]
