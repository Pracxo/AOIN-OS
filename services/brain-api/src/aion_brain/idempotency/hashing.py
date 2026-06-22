"""Deterministic hashing helpers for idempotency."""

import hashlib
import json
from typing import Any

DEFAULT_IGNORED_FIELDS = {"timestamp", "created_at", "updated_at", "trace_id", "correlation_id"}


def normalize_json(value: dict[str, Any], ignore_fields: set[str] | None = None) -> str:
    """Return a stable JSON string for semantically equivalent payloads."""
    ignored = ignore_fields or set()
    normalized = _normalize(value, ignored)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), default=str)


def sha256_json(value: dict[str, Any], ignore_fields: set[str] | None = None) -> str:
    """Return a deterministic SHA-256 hash for a JSON-like dict."""
    return hashlib.sha256(normalize_json(value, ignore_fields).encode("utf-8")).hexdigest()


def sha256_response(value: dict[str, Any]) -> str:
    """Return a deterministic response hash."""
    return sha256_json(value)


def _normalize(value: Any, ignored: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalize(nested, ignored)
            for key, nested in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key) not in ignored
        }
    if isinstance(value, list):
        return [_normalize(item, ignored) for item in value]
    return value
