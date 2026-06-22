"""Deterministic hashing for release candidate reports and evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aion_brain.release_candidate.redaction import redact_rc_payload


def canonical_rc_json(value: dict[str, Any]) -> str:
    """Return deterministic JSON after redaction."""

    redacted = redact_rc_payload(value)
    return json.dumps(redacted, sort_keys=True, separators=(",", ":"), default=str)


def hash_rc_report(value: dict[str, Any]) -> str:
    """Return a sha256 hash of a redacted RC report."""

    return hashlib.sha256(canonical_rc_json(value).encode("utf-8")).hexdigest()


def hash_check_evidence(value: dict[str, Any]) -> str:
    """Return a sha256 hash of redacted check evidence."""

    return hashlib.sha256(canonical_rc_json(value).encode("utf-8")).hexdigest()


__all__ = ["canonical_rc_json", "hash_check_evidence", "hash_rc_report"]
