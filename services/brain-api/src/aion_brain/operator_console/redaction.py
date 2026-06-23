"""Redaction helpers for read-only operator console view models."""

from __future__ import annotations

from typing import Any

REDACTED = "[redacted]"
_SENSITIVE_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "chain_of_thought",
    "credential",
    "hidden_reasoning",
    "password",
    "private_key",
    "provider_payload",
    "raw_model_payload",
    "raw_prompt",
    "secret",
    "token",
}
_SENSITIVE_TEXT_MARKERS = (
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
    "raw_prompt",
    "raw prompt",
    "hidden_reasoning",
    "hidden reasoning",
    "chain-of-thought",
    "chain_of_thought",
)


def redact_console_payload(value: Any) -> Any:
    """Return a redacted copy of an arbitrary console payload."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            redacted[str(key)] = (
                REDACTED if _is_sensitive_key(str(key)) else redact_console_payload(nested)
            )
        return redacted
    if isinstance(value, list):
        return [redact_console_payload(item) for item in value]
    if isinstance(value, str):
        return REDACTED if _is_sensitive_text(value) else value
    return value


def payload_has_sensitive_content(value: Any) -> bool:
    """Return true when a payload contains data unsafe for console display."""
    if isinstance(value, dict):
        return any(
            _is_sensitive_key(str(key)) or payload_has_sensitive_content(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(payload_has_sensitive_content(item) for item in value)
    if isinstance(value, str):
        return _is_sensitive_text(value)
    return False


def _is_sensitive_key(value: str) -> bool:
    normalized = value.lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _is_sensitive_text(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _SENSITIVE_TEXT_MARKERS)


__all__ = ["REDACTED", "payload_has_sensitive_content", "redact_console_payload"]
