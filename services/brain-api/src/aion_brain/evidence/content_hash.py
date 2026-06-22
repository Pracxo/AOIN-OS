"""Content hashing utilities for AION Evidence Vault."""

import hashlib


def normalize_text_for_hash(text: str) -> str:
    """Normalize text for stable content addressing without changing meaning."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n"))


def sha256_text(text: str) -> str:
    """Return SHA-256 for normalized UTF-8 text."""
    return sha256_bytes(normalize_text_for_hash(text).encode("utf-8"))


def sha256_bytes(data: bytes) -> str:
    """Return SHA-256 for bytes."""
    return hashlib.sha256(data).hexdigest()
