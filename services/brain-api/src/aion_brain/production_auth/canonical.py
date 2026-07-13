"""Canonical serialization for disabled production-auth evidence."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for supported evidence values."""

    return canonical_json_text(value).encode("utf-8")


def canonical_json_text(value: Any) -> str:
    """Return deterministic compact JSON text for supported evidence values."""

    normalized = _normalize(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_fingerprint(value: Any) -> str:
    """Return a SHA-256 fingerprint of the canonical evidence payload."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _normalize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _normalize(value.model_dump(mode="python"))
    if is_dataclass(value) and not isinstance(value, type):
        return _normalize(asdict(value))
    if isinstance(value, datetime):
        converted = value
        if converted.tzinfo is None:
            converted = converted.replace(tzinfo=UTC)
        converted = converted.astimezone(UTC)
        return converted.isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise TypeError("canonical JSON does not support non-finite decimals")
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("canonical JSON does not support NaN or infinity")
        return value
    if isinstance(value, str | int | bool) or value is None:
        return value
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, nested in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            normalized[key] = _normalize(nested)
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_normalize(item) for item in value]
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


__all__ = ["canonical_json_bytes", "canonical_json_text", "sha256_fingerprint"]
