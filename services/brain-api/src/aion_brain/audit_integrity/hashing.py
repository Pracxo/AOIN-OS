"""Deterministic sha256 hashing for the audit chain."""

from __future__ import annotations

import hashlib
from typing import Any

from aion_brain.audit_integrity.canonical import canonical_json, canonicalize_payload


def sha256_text(value: str) -> str:
    """Hash text with sha256."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_payload(payload: dict[str, Any]) -> str:
    """Hash canonical payload JSON."""
    return sha256_text(canonical_json(canonicalize_payload(payload)))


def hash_entry(
    previous_hash: str | None,
    payload_hash: str,
    sequence_number: int,
    metadata: dict[str, Any],
) -> str:
    """Hash one audit entry link."""
    return sha256_text(
        canonical_json(
            {
                "metadata": metadata,
                "payload_hash": payload_hash,
                "previous_hash": previous_hash,
                "sequence_number": sequence_number,
            }
        )
    )


def hash_checkpoint(entry_hashes: list[str], previous_checkpoint_hash: str | None) -> str:
    """Hash a checkpoint over ordered audit entry hashes."""
    return sha256_text(
        canonical_json(
            {
                "entry_hashes": entry_hashes,
                "previous_checkpoint_hash": previous_checkpoint_hash,
            }
        )
    )
