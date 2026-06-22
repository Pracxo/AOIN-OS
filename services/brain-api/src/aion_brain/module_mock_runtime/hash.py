"""Deterministic hashing helpers for module mock runtime."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aion_brain.module_mock_runtime.redaction import redact_module_mock_payload


def canonical_mock_json(value: dict[str, Any]) -> str:
    """Return stable JSON after redaction."""

    return json.dumps(redact_module_mock_payload(value), sort_keys=True, separators=(",", ":"))


def hash_mock_payload(value: dict[str, Any]) -> str:
    """Hash a redacted input payload."""

    return hashlib.sha256(canonical_mock_json(value).encode("utf-8")).hexdigest()


def hash_mock_output(value: dict[str, Any]) -> str:
    """Hash a redacted synthetic output payload."""

    return hashlib.sha256(canonical_mock_json(value).encode("utf-8")).hexdigest()


__all__ = ["canonical_mock_json", "hash_mock_output", "hash_mock_payload"]
