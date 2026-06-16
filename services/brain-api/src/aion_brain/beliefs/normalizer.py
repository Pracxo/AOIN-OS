"""Deterministic claim normalization helpers."""

from __future__ import annotations

import hashlib
import re

from aion_brain.contracts.beliefs import text_has_hidden_markers, text_has_secret_markers

_WHITESPACE = re.compile(r"\s+")
_TRAILING_PUNCTUATION = ".!;:"


def normalize_claim_text(text: str) -> str:
    """Normalize claim text without removing semantic negation."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip().lower()
    normalized = _WHITESPACE.sub(" ", normalized)
    return normalized.rstrip(_TRAILING_PUNCTUATION).strip()


def hash_normalized_claim(normalized: str) -> str:
    """Return a deterministic hash for normalized claim text."""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def is_claim_text_safe(text: str) -> bool:
    """Return false for hidden reasoning, raw prompts, or obvious raw secrets."""
    if not text.strip():
        return False
    return not text_has_hidden_markers(text) and not text_has_secret_markers(text)
