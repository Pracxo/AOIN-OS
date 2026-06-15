"""Cursor helpers for AION SDK callers."""

from __future__ import annotations

import base64
import json
from typing import Any


def encode_cursor(values: dict[str, Any]) -> str:
    """Encode a URL-safe JSON cursor."""

    raw = json.dumps(values, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a URL-safe JSON cursor."""

    padding = "=" * (-len(cursor) % 4)
    raw = base64.urlsafe_b64decode((cursor + padding).encode())
    value = json.loads(raw.decode())
    if not isinstance(value, dict):
        raise ValueError("cursor must decode to an object")
    return value

