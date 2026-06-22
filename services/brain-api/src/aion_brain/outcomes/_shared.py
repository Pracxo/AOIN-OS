"""Shared helpers for outcome services."""

from __future__ import annotations

from typing import Any

from aion_brain.decisions._shared import (
    audit_optional,
    authorize,
    emit_telemetry,
    provenance_optional,
    scope_matches,
)


def call_optional(
    target: object | None,
    names: tuple[str, ...],
    *args: object,
    **kwargs: object,
) -> Any:
    """Call the first available method, swallowing optional integration failures."""
    for name in names:
        method = getattr(target, name, None)
        if callable(method):
            try:
                return method(*args, **kwargs)
            except Exception:
                return None
    return None


def clamp_score(value: float) -> float:
    """Clamp a score to AION's public 0..1 range."""
    return max(0.0, min(1.0, value))


__all__ = [
    "audit_optional",
    "authorize",
    "call_optional",
    "clamp_score",
    "emit_telemetry",
    "provenance_optional",
    "scope_matches",
]
