"""Golden path redaction helpers."""

from __future__ import annotations

from typing import Any

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
_HIDDEN_KEYS = {
    "raw_prompt",
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "cot",
}
_HIDDEN_VALUE_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
)


def redact_golden_path_payload(value: object) -> object:
    """Return a display-safe copy of golden path payload data."""

    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _HIDDEN_KEYS or any(part in lowered for part in _SECRET_KEY_PARTS):
                redacted[str(key)] = "[redacted]"
                continue
            redacted[str(key)] = redact_golden_path_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_golden_path_payload(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
            return "[redacted]"
        if any(marker in lowered for marker in _HIDDEN_VALUE_MARKERS):
            return "[redacted]"
    return value


def safe_summary(value: object) -> dict[str, Any]:
    """Return a dict summary safe for persistence and UI display."""

    redacted = redact_golden_path_payload(value)
    if isinstance(redacted, dict):
        return dict(redacted)
    return {"value": redacted}


__all__ = ["redact_golden_path_payload", "safe_summary"]
