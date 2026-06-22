"""Redaction helpers for registry descriptors and reports."""

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
    "system_prompt",
    "token",
}
_SECRET_VALUE_MARKERS = (
    "api_key=",
    "password=",
    "secret=",
    "sk-",
    "token=",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
)
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
    "ignore previous instructions",
)
_REDACTED = "[redacted]"


def redact_registry_text(value: str) -> str:
    """Redact unsafe registry text without retaining removed raw values."""
    lowered = value.lower()
    if any(marker in lowered for marker in (*_SECRET_VALUE_MARKERS, *_HIDDEN_MARKERS)):
        return _REDACTED
    return value.strip()


def redact_registry_payload(value: Any) -> Any:
    """Redact secret-like values recursively."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                redacted[str(key)] = _REDACTED
            else:
                redacted[str(key)] = redact_registry_payload(nested)
        return redacted
    if isinstance(value, list):
        return [redact_registry_payload(item) for item in value]
    if isinstance(value, str):
        return redact_registry_text(value)
    return value


def redact_registry_refs(refs: list[str]) -> list[str]:
    """Redact unsafe refs."""
    redacted: list[str] = []
    for ref in refs:
        safe_ref = redact_registry_text(ref)
        if safe_ref != _REDACTED:
            redacted.append(safe_ref)
    return redacted


__all__ = ["redact_registry_payload", "redact_registry_refs", "redact_registry_text"]
