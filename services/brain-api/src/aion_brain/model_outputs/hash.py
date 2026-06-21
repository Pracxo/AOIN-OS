"""Deterministic model output hashing helpers."""

from __future__ import annotations

import hashlib


def normalize_model_output(text: str) -> str:
    """Normalize line endings and trailing whitespace."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n")).strip()


def hash_model_output(text: str) -> str:
    """Return sha256 hash for normalized model output."""

    return hashlib.sha256(normalize_model_output(text).encode("utf-8")).hexdigest()


def hash_output_segment(text: str) -> str:
    """Return sha256 hash for one normalized segment."""

    return hash_model_output(text)


def estimate_output_tokens(text: str) -> int:
    """Deterministic token estimate."""

    char_count = len(text)
    return max(1, (char_count + 3) // 4) if char_count else 0


__all__ = [
    "estimate_output_tokens",
    "hash_model_output",
    "hash_output_segment",
    "normalize_model_output",
]
