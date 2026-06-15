"""Deterministic visual intensity and status helpers."""

import math
from datetime import datetime
from typing import cast

from aion_brain.contracts.visual import BrainVisualNodeType, BrainVisualStatus

ALLOWED_NODE_TYPES = {
    "event",
    "intent",
    "context",
    "memory",
    "graph",
    "evidence",
    "chunk",
    "claim",
    "retrieval",
    "reasoning",
    "model",
    "plan",
    "policy",
    "risk",
    "guardrail",
    "governance",
    "conflict",
    "compaction",
    "retention",
    "execution",
    "step",
    "approval",
    "capability",
    "module",
    "runtime",
    "goal",
    "task",
    "schedule",
    "reflection",
    "candidate",
    "skill",
    "actor",
    "workspace",
    "permission",
    "scope",
    "evaluation",
    "learning",
    "trace",
    "telemetry",
    "unknown",
}


def clamp_intensity(value: float) -> float:
    """Clamp an intensity value to the public contract range."""
    return max(0.0, min(1.0, value))


def apply_time_decay(
    intensity: float,
    event_time: datetime,
    now: datetime,
    half_life_seconds: int,
) -> float:
    """Apply deterministic exponential half-life decay."""
    if half_life_seconds <= 0:
        return clamp_intensity(intensity)
    elapsed = max(0.0, (now - event_time).total_seconds())
    return clamp_intensity(intensity * math.pow(0.5, elapsed / half_life_seconds))


def status_from_event_type(event_type: str) -> BrainVisualStatus:
    """Map a generic telemetry event name to visual status."""
    normalized = event_type.lower()
    if "blocked" in normalized or "denied" in normalized:
        return "blocked"
    if "failed" in normalized or "error" in normalized:
        return "failed"
    if any(term in normalized for term in ("completed", "created", "resolved", "promoted")):
        return "completed"
    if any(term in normalized for term in ("started", "activated", "selected", "checked")):
        return "active"
    return "active"


def node_type_from_telemetry(
    node_type: str | None,
    event_type: str,
) -> BrainVisualNodeType:
    """Normalize telemetry node types without domain-specific rules."""
    if node_type in ALLOWED_NODE_TYPES:
        return cast(BrainVisualNodeType, node_type)
    prefix = event_type.split("_", maxsplit=1)[0]
    if prefix in ALLOWED_NODE_TYPES:
        return cast(BrainVisualNodeType, prefix)
    return "unknown"
