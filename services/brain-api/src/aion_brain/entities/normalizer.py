"""Deterministic entity normalization."""

from __future__ import annotations

import re
import unicodedata


def normalize_entity_name(value: str) -> str:
    """Return a stable, domain-neutral normalized entity name."""
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"['`]", "", normalized)
    normalized = re.sub(r"[^a-z0-9._:/ -]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def lexical_tokens(value: str) -> set[str]:
    """Return generic lexical tokens for deterministic matching."""
    return set(re.findall(r"[a-z0-9]+", normalize_entity_name(value)))
