"""Deterministic hashing helpers for dialogue content."""

from __future__ import annotations

from hashlib import sha256


def normalize_message_content(content: str) -> str:
    """Normalize line endings and strip trailing whitespace deterministically."""

    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def hash_message_content(content: str) -> str:
    """Return a sha256 digest of normalized dialogue content."""

    normalized = normalize_message_content(content)
    return sha256(normalized.encode("utf-8")).hexdigest()
