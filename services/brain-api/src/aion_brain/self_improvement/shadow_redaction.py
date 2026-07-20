"""Redaction and safety checks for self-improvement shadow inputs."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

from aion_brain.contracts.self_improvement_shadow import (
    canonical_shadow_fingerprint,
    normalize_shadow_marker,
    require_utc_datetime,
    validate_shadow_text,
)

_FORBIDDEN_MARKERS = (
    "password",
    "credential",
    "authorization",
    "bearer",
    "access token",
    "refresh token",
    "session token",
    "cookie",
    "client secret",
    "private key",
    "signing key",
    "raw prompt",
    "hidden reasoning",
    "chain of thought",
    "raw user message",
    "provider payload",
    "source patch",
    "raw diff",
    "personal data",
    "email address",
    "phone number",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_shadow_safe_value(value: Any) -> Any:
    """Validate and return a normalized immutable shadow-safe value."""

    return _normalize_safe_value(value, seen=set())


def redact_shadow_summary(value: Any) -> str:
    """Return a bounded summary for safe shadow evidence."""

    safe = validate_shadow_safe_value(value)
    if isinstance(safe, str):
        return validate_shadow_text(safe, max_length=512)
    fingerprint = canonical_shadow_fingerprint(safe)
    return f"redacted shadow evidence {fingerprint[:16]}"


def shadow_safe_fingerprint(value: Any) -> str:
    """Return a deterministic fingerprint for semantically identical safe values."""

    return canonical_shadow_fingerprint(validate_shadow_safe_value(value))


def _normalize_safe_value(value: Any, *, seen: set[int]) -> Any:
    if isinstance(value, bool | int) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("shadow value must be finite")
        return value
    if isinstance(value, str):
        return _safe_text(value)
    if isinstance(value, datetime):
        return require_utc_datetime(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bytes | bytearray | memoryview):
        raise ValueError("shadow value type is not allowed")
    if isinstance(value, BaseException):
        raise ValueError("shadow value type is not allowed")
    if callable(value):
        raise ValueError("shadow value type is not allowed")

    value_id = id(value)
    if value_id in seen:
        raise ValueError("recursive shadow value is not allowed")
    seen.add(value_id)
    try:
        if isinstance(value, Mapping):
            normalized: dict[str, Any] = {}
            for key, nested in value.items():
                if not isinstance(key, str):
                    raise ValueError("shadow mapping keys must be strings")
                safe_key = _safe_key(key)
                if safe_key in normalized:
                    raise ValueError("duplicate normalized shadow key")
                normalized[safe_key] = _normalize_safe_value(nested, seen=seen)
            return normalized
        if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
            return tuple(_normalize_safe_value(item, seen=seen) for item in value)
    finally:
        seen.remove(value_id)
    raise ValueError("shadow value type is not allowed")


def _safe_key(value: str) -> str:
    normalized = normalize_shadow_marker(value)
    if not normalized:
        raise ValueError("shadow key cannot be empty")
    if any(marker in normalized for marker in _FORBIDDEN_MARKERS):
        raise ValueError("shadow key contains prohibited material")
    return normalized.replace(" ", "_")


def _safe_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    if _SHA256_RE.fullmatch(normalized):
        return normalized
    return validate_shadow_text(normalized, max_length=4096)


__all__ = [
    "redact_shadow_summary",
    "shadow_safe_fingerprint",
    "validate_shadow_safe_value",
]
