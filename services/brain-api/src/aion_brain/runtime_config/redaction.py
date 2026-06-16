"""Runtime configuration redaction helpers."""

from __future__ import annotations

from typing import Any

SENSITIVE_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
    "authorization",
    "bearer",
)


def contains_sensitive_key(key: str) -> bool:
    """Return whether a config key is sensitive."""
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS) or (
        normalized.endswith("_url") and "database" in normalized
    )


def redact_config_value(key: str, value: Any) -> Any:
    """Redact sensitive config values."""
    if contains_sensitive_key(key):
        return {"redacted": True}
    if isinstance(value, dict):
        return sanitize_config_dict(value)
    if isinstance(value, list):
        return [sanitize_config_dict(item) if isinstance(item, dict) else item for item in value]
    return value


def sanitize_config_dict(value: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with secret-like values redacted."""
    return {str(key): redact_config_value(str(key), item) for key, item in value.items()}
