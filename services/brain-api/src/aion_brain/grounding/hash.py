"""Deterministic grounding hash helpers."""

from __future__ import annotations

import hashlib
import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_source_text(text: str) -> str:
    """Normalize source text for deterministic comparison and hashing."""

    return _WHITESPACE_RE.sub(" ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def hash_source_content(text: str) -> str:
    """Return a sha256 hash of normalized source content."""

    return hashlib.sha256(normalize_source_text(text).encode("utf-8")).hexdigest()


def hash_statement(text: str) -> str:
    """Return a sha256 hash of a normalized statement."""

    return hashlib.sha256(normalize_source_text(text).lower().encode("utf-8")).hexdigest()


__all__ = ["hash_source_content", "hash_statement", "normalize_source_text"]
