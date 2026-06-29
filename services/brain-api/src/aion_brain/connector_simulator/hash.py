"""Stable hashing helpers for connector simulator evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash(value: Any) -> str:
    """Return a deterministic SHA-256 hash for JSON-compatible data."""

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


__all__ = ["stable_hash"]
