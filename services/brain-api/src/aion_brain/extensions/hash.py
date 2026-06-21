"""Stable hashing helpers for extension manifests."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aion_brain.extensions.redaction import redact_extension_payload


def canonical_manifest_json(manifest: dict[str, Any]) -> str:
    """Return deterministic JSON for a redacted manifest."""

    redacted = redact_extension_payload(manifest)
    return json.dumps(redacted, sort_keys=True, separators=(",", ":"), default=str)


def hash_manifest(manifest: dict[str, Any]) -> str:
    """Return the sha256 hash of a redacted manifest."""

    return hashlib.sha256(canonical_manifest_json(manifest).encode("utf-8")).hexdigest()


def hash_extension_schema(value: dict[str, Any]) -> str:
    """Return a stable hash for extension-declared schema metadata."""

    return hash_manifest(value)


__all__ = ["canonical_manifest_json", "hash_extension_schema", "hash_manifest"]
