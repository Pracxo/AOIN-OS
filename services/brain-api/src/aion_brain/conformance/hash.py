"""Deterministic hashing for conformance records."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aion_brain.conformance.redaction import redact_conformance_payload


def canonical_conformance_json(value: dict[str, Any]) -> str:
    """Return sorted, redacted canonical JSON."""

    return json.dumps(redact_conformance_payload(value), sort_keys=True, separators=(",", ":"))


def hash_test_vector(value: dict[str, Any]) -> str:
    """Hash a test vector payload."""

    return _hash(value)


def hash_mock_input(value: dict[str, Any]) -> str:
    """Hash mock invocation input."""

    return _hash(value)


def _hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_conformance_json(value).encode("utf-8")).hexdigest()


__all__ = ["canonical_conformance_json", "hash_mock_input", "hash_test_vector"]
