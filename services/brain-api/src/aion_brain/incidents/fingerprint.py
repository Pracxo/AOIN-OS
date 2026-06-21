"""Deterministic incident correlation keys and fingerprints."""

from __future__ import annotations

import hashlib
import re


def normalize_signal_summary(summary: str) -> str:
    """Normalize free-text summaries for deterministic grouping."""

    cleaned = re.sub(r"[^a-z0-9]+", " ", summary.lower())
    return " ".join(cleaned.split())


def build_signal_fingerprint(
    source_type: str,
    source_id: str,
    signal_type: str,
    summary: str,
) -> str:
    """Build a stable SHA-256 fingerprint for a signal."""

    payload = "|".join(
        [
            source_type.strip().lower(),
            source_id.strip().lower(),
            signal_type.strip().lower(),
            normalize_signal_summary(summary),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_correlation_key(
    source_type: str,
    signal_type: str,
    trace_id: str | None,
    target_ref: str | None = None,
) -> str:
    """Build a human-readable stable correlation key."""

    trace_part = trace_id or "no-trace"
    target_part = target_ref or "source"
    return ":".join(
        [
            "incident",
            source_type.strip().lower(),
            signal_type.strip().lower(),
            trace_part.strip().lower(),
            target_part.strip().lower(),
        ]
    )


__all__ = [
    "build_correlation_key",
    "build_signal_fingerprint",
    "normalize_signal_summary",
]
