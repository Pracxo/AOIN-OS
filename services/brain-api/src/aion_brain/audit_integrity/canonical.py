"""Canonical JSON helpers for audit hashing."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from aion_brain.audit_integrity.redaction import strip_chain_of_thought

_VOLATILE_FIELDS = {"request_duration_ms", "transient_latency_ms"}


def canonicalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize an audit payload before hashing."""
    cleaned = strip_chain_of_thought(payload)
    normalized = _normalize(cleaned)
    return dict(normalized) if isinstance(normalized, dict) else {}


def canonical_json(value: dict[str, Any] | list[Any] | str | int | float | bool | None) -> str:
    """Return stable compact JSON text for hashing."""
    return json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _normalize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        volatile = {
            str(item) for item in value.get("_volatile_fields", []) if isinstance(item, str)
        }
        result: dict[str, Any] = {}
        for key in sorted(value):
            if key == "_volatile_fields":
                continue
            if key in _VOLATILE_FIELDS and key in volatile:
                continue
            result[str(key)] = _normalize(value[key])
        return result
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value
