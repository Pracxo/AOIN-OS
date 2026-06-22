"""Release candidate redaction helpers."""

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
_REMOVED_KEYS = {
    "raw_prompt",
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "private_reasoning",
    "cot",
}
_REMOVED_VALUE_MARKERS = (
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


def redact_rc_payload(value: object) -> object:
    """Return a display-safe copy of RC evidence and reports."""

    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _REMOVED_KEYS:
                continue
            if any(part in normalized for part in _SECRET_KEY_PARTS):
                continue
            redacted[str(key)] = redact_rc_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_rc_payload(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
            return "[redacted]"
        if any(marker in lowered for marker in _REMOVED_VALUE_MARKERS):
            return "[redacted]"
    return value


def safe_rc_summary(value: object) -> dict[str, Any]:
    """Return a dict summary safe for local operator display."""

    redacted = _json_compatible(redact_rc_payload(value))
    if isinstance(redacted, dict):
        return dict(redacted)
    return {"value": redacted}


def _json_compatible(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_compatible(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


__all__ = ["redact_rc_payload", "safe_rc_summary"]
