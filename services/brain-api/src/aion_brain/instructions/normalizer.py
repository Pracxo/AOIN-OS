"""Instruction and preference normalization helpers."""

from __future__ import annotations

import re

from aion_brain.contracts.concepts import text_has_secret_markers
from aion_brain.contracts.instructions import (
    text_has_forbidden_override_markers,
    text_has_hidden_reasoning_markers,
)
from aion_brain.contracts.preferences import normalize_preference_key

_HIDDEN_MARKERS = (
    "chain_of_thought",
    "chain-of-thought",
    "chain of thought",
    "hidden_reasoning",
    "hidden reasoning",
    "private reasoning",
    "raw_prompt",
    "raw prompt",
)


def normalize_instruction_text(value: str) -> str:
    """Normalize text deterministically and remove hidden-reasoning markers."""

    normalized = re.sub(r"\s+", " ", value.strip().lower())
    for marker in _HIDDEN_MARKERS:
        normalized = normalized.replace(marker, "")
    return re.sub(r"\s+", " ", normalized).strip()


def is_safe_instruction_text(value: str) -> bool:
    """Return true when instruction text is public-safe and non-overriding."""

    if not value.strip():
        return False
    if text_has_secret_markers(value):
        return False
    if text_has_hidden_reasoning_markers(value):
        return False
    return not text_has_forbidden_override_markers(value)


def detect_forbidden_override_attempt(value: str) -> list[str]:
    """Return generic override categories detected in instruction text."""

    lowered = value.lower()
    reasons: list[str] = []
    checks = {
        "policy": ("ignore policy", "override policy", "bypass policy", "disable policy"),
        "approval": ("bypass approval", "skip approval", "ignore approval", "override approval"),
        "autonomy": ("disable autonomy", "override autonomy", "ignore autonomy"),
        "runtime_config": ("ignore runtime config", "override runtime config"),
        "sandbox": ("ignore sandbox", "bypass sandbox"),
        "capability": ("ignore capability limits", "bypass capability"),
        "secrets": ("expose secrets", "show secrets"),
        "hidden_reasoning": _HIDDEN_MARKERS,
    }
    for reason, markers in checks.items():
        if any(marker in lowered for marker in markers):
            reasons.append(reason)
    if not reasons and (
        text_has_forbidden_override_markers(value) or text_has_hidden_reasoning_markers(value)
    ):
        reasons.append("generic")
    return reasons


__all__ = [
    "detect_forbidden_override_attempt",
    "is_safe_instruction_text",
    "normalize_instruction_text",
    "normalize_preference_key",
]
