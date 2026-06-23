"""Stable hashing helpers for provider hardening records."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def hash_provider_payload(payload: dict[str, Any]) -> str:
    """Return a deterministic hash for local-only provider simulation payloads."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


__all__ = ["hash_provider_payload"]
