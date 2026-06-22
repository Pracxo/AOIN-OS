"""Deterministic checksum helpers for local backups."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_jsonl_records(records: list[dict[str, Any]]) -> str:
    """Return a deterministic checksum for JSONL records."""
    digest = hashlib.sha256()
    for record in _sorted_records(records):
        encoded = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        digest.update(encoded)
        digest.update(b"\n")
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum of a local file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def root_checksum(checksums: dict[str, str]) -> str:
    """Return a deterministic checksum over child checksums."""
    digest = hashlib.sha256()
    for path, checksum in sorted(checksums.items()):
        digest.update(f"{path}:{checksum}\n".encode())
    return digest.hexdigest()


def _sorted_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=_record_sort_key)


def _record_sort_key(record: dict[str, Any]) -> tuple[str, str]:
    for key in ("id", "event_id", "memory_id", "trace_id", "record_id"):
        value = record.get(key)
        if value is not None:
            return (key, str(value))
    return ("", json.dumps(record, sort_keys=True, default=str))
