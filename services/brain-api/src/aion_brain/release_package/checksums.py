"""Deterministic checksum helpers for local release packaging."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 checksum for bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: dict[str, Any]) -> str:
    """Return the SHA-256 checksum for JSON-compatible data."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256_bytes(encoded)


def root_checksum(file_checksums: dict[str, str]) -> str:
    """Return a stable checksum over path-to-checksum mappings."""
    digest = hashlib.sha256()
    for path in sorted(file_checksums):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_checksums[path].encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
