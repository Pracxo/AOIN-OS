"""Deterministic schema hashing for AION Contract Registry."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aion_brain.contract_registry.redaction import redact_contract_payload


def canonical_schema_json(value: dict[str, Any]) -> str:
    """Serialize a redacted schema with stable key ordering."""

    redacted = redact_contract_payload(value)
    return json.dumps(redacted, sort_keys=True, separators=(",", ":"), default=str)


def hash_schema(value: dict[str, Any]) -> str:
    """Hash a redacted schema payload with sha256."""

    return hashlib.sha256(canonical_schema_json(value).encode("utf-8")).hexdigest()


def hash_manifest(items: list[dict[str, Any]]) -> str:
    """Hash a deterministic list of manifest entries."""

    redacted = [redact_contract_payload(item) for item in items]
    body = json.dumps(redacted, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


__all__ = ["canonical_schema_json", "hash_manifest", "hash_schema"]
