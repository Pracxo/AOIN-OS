"""Deterministic prompt hashing helpers."""

from __future__ import annotations

import hashlib

from aion_brain.contracts.prompts import PromptSection


def normalize_prompt_text(text: str) -> str:
    """Normalize line endings and trailing whitespace without reordering text."""

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


def hash_prompt_text(text: str) -> str:
    """Return a deterministic sha256 hash of normalized prompt text."""

    normalized = normalize_prompt_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_prompt_sections(sections: list[PromptSection]) -> str:
    """Return a deterministic hash preserving section order."""

    rendered = "\n\n".join(
        f"[{section.section_type}:{section.section_id}]\n{section.content}" for section in sections
    )
    return hash_prompt_text(rendered)


__all__ = ["hash_prompt_sections", "hash_prompt_text", "normalize_prompt_text"]
