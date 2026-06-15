"""Deterministic runtime configuration hashing."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aion_brain.runtime_config.redaction import sanitize_config_dict


def normalize_config(value: dict[str, Any]) -> str:
    """Return deterministic JSON for configuration payloads."""
    redacted = sanitize_config_dict(value)
    return json.dumps(redacted, sort_keys=True, separators=(",", ":"), default=str)


def hash_config_snapshot(
    settings: dict[str, Any],
    feature_flags: dict[str, bool],
    adapter_status: dict[str, Any],
) -> str:
    """Return a deterministic hash of a redacted snapshot."""
    payload = {
        "settings": settings,
        "feature_flags": feature_flags,
        "adapter_status": adapter_status,
    }
    return hashlib.sha256(normalize_config(payload).encode("utf-8")).hexdigest()
