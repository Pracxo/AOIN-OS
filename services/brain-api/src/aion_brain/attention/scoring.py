"""Deterministic attention scoring."""

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.attention import AttentionSignal
from aion_brain.contracts.working_memory import WorkingMemorySlot

_RISK_VALUES = {
    "low": 0.20,
    "medium": 0.45,
    "high": 0.75,
    "critical": 0.95,
}


def score_attention_signal(signal: AttentionSignal, now: datetime | None = None) -> float:
    """Score one attention signal deterministically."""
    current = now or datetime.now(UTC)
    recency = _recency_score(signal.created_at, current)
    risk = _RISK_VALUES.get(signal.risk_level, 0.45)
    score = (
        signal.urgency * 0.35
        + signal.importance * 0.30
        + signal.confidence * 0.15
        + recency * 0.10
        + risk * 0.10
    )
    return _clamp(score)


def score_working_memory_slot(slot: WorkingMemorySlot, now: datetime | None = None) -> float:
    """Score one working memory slot deterministically."""
    current = now or datetime.now(UTC)
    if slot.deleted_at is not None:
        return 0.0
    if _expired(slot, current) and not slot.pinned:
        return 0.0
    score = (
        slot.priority * 0.45
        + slot.confidence * 0.25
        + (0.15 if slot.pinned else 0.0)
        + _recency_score(slot.created_at, current) * 0.10
        + _expiry_urgency(slot, current) * 0.05
    )
    if slot.pinned:
        return _clamp(max(0.5, score))
    return _clamp(score)


def _recency_score(created_at: datetime | None, now: datetime) -> float:
    if created_at is None:
        return 0.4
    created = created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=UTC)
    age = now - created
    if age <= timedelta(minutes=5):
        return 1.0
    if age <= timedelta(hours=1):
        return 0.7
    if age <= timedelta(hours=24):
        return 0.4
    return 0.2


def _expiry_urgency(slot: WorkingMemorySlot, now: datetime) -> float:
    if slot.pinned or slot.expires_at is None:
        return 0.0
    expires_at = (
        slot.expires_at
        if slot.expires_at.tzinfo is not None
        else slot.expires_at.replace(tzinfo=UTC)
    )
    remaining = expires_at - now
    if remaining <= timedelta(minutes=5):
        return 1.0
    if remaining <= timedelta(hours=1):
        return 0.6
    if remaining <= timedelta(hours=24):
        return 0.3
    return 0.1


def _expired(slot: WorkingMemorySlot, now: datetime) -> bool:
    if slot.expires_at is None:
        return False
    expires_at = (
        slot.expires_at
        if slot.expires_at.tzinfo is not None
        else slot.expires_at.replace(tzinfo=UTC)
    )
    return expires_at <= now


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
