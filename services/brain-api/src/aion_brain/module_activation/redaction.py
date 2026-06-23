"""Redaction helpers for module activation metadata."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.model_outputs import reject_secret_like_payload

_REDACTED = "[redacted]"
_SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "bearer",
    "chain_of_thought",
    "hidden_reasoning",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}


def redact_activation_payload(value: Any) -> Any:
    """Return a redacted, JSON-compatible activation metadata payload."""

    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in _SENSITIVE_KEYS):
                cleaned[str(key)] = _REDACTED
            else:
                cleaned[str(key)] = redact_activation_payload(nested)
        return cleaned
    if isinstance(value, list):
        return [redact_activation_payload(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if "sk-" in lowered or "hidden reasoning" in lowered or "raw prompt" in lowered:
            return _REDACTED
    return value


def assert_activation_payload_safe(value: Any) -> None:
    """Reject secret-like payloads after redaction boundaries are applied."""

    reject_secret_like_payload(value)


__all__ = ["assert_activation_payload_safe", "redact_activation_payload"]
