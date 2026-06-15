"""Secret-safe redaction helpers for local backups."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.backups import BackupRedactionMode

SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "credential",
    "authorization",
    "bearer",
)
METADATA_ONLY_KEYS = {
    "id",
    "event_id",
    "memory_id",
    "trace_id",
    "correlation_id",
    "type",
    "event_type",
    "resource_type",
    "status",
    "created_at",
    "updated_at",
    "timestamp",
    "workspace_id",
    "actor_id",
    "owner_scope",
}
REDACTED = "[REDACTED]"


def contains_sensitive_key(value: Any) -> bool:
    """Return true when a mapping contains secret-like keys at any depth."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS):
                return True
            if contains_sensitive_key(item):
                return True
    if isinstance(value, list):
        return any(contains_sensitive_key(item) for item in value)
    return False


def strip_sensitive_metadata(value: dict[str, Any]) -> dict[str, Any]:
    """Drop secret-like metadata keys at any nesting depth."""
    sanitized: dict[str, Any] = {}
    for key, item in value.items():
        normalized = str(key).lower().replace("-", "_")
        if any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS):
            continue
        if isinstance(item, dict):
            sanitized[str(key)] = strip_sensitive_metadata(item)
        elif isinstance(item, list):
            sanitized[str(key)] = [
                strip_sensitive_metadata(element) if isinstance(element, dict) else element
                for element in item
            ]
        else:
            sanitized[str(key)] = item
    return sanitized


def redact_record(record: dict[str, Any], mode: BackupRedactionMode) -> dict[str, Any] | None:
    """Return a redacted record or None when exclusion mode skips it."""
    if mode == "none":
        return dict(record)
    if mode == "metadata_only":
        return _metadata_only(record)
    if mode == "exclude_sensitive":
        if str(record.get("sensitivity", "")).lower() == "restricted":
            return None
        if contains_sensitive_key(record):
            return None
        return dict(record)
    redacted = _redact_sensitive(record)
    return redacted if isinstance(redacted, dict) else {}


def _metadata_only(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key in METADATA_ONLY_KEYS}


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS):
                sanitized[str(key)] = REDACTED
            else:
                sanitized[str(key)] = _redact_sensitive(item)
        return sanitized
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value
