"""Deterministic concept normalization."""

from __future__ import annotations

import re
import unicodedata


def normalize_concept_name(value: str) -> str:
    """Return a stable normalized concept name."""
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[^a-z0-9._:/ -]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()
