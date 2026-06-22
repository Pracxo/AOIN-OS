"""Notification redaction helpers."""

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
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
_HIDDEN_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
    "raw prompt",
    "raw_prompt",
    "system prompt:",
    "developer prompt:",
)


def redact_text(value: str) -> str:
    """Return safe operator-display text."""

    lowered = value.lower()
    if any(marker in lowered for marker in _HIDDEN_MARKERS):
        return "[redacted hidden reasoning or raw prompt]"
    if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
        return "[redacted secret-like value]"
    return value


def redact_payload(value: Any) -> Any:
    """Remove secret-like keys and values from notification payloads."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                redacted[f"redacted_field_{len(redacted) + 1}"] = "[redacted]"
            else:
                redacted[str(key)] = redact_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


__all__ = ["redact_payload", "redact_text"]
