"""Attention scoring tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.attention.scoring import score_attention_signal, score_working_memory_slot
from tests.test_attention_contracts import attention_signal
from tests.test_working_memory_contracts import working_memory_slot


def test_attention_scoring_ranks_urgent_high_risk_signal_above_low_priority() -> None:
    """Urgency, importance, and risk raise attention priority."""
    now = datetime.now(UTC)
    urgent = attention_signal(
        urgency=0.95,
        importance=0.9,
        confidence=0.9,
        risk_level="high",
        created_at=now,
    )
    low = attention_signal(
        urgency=0.1,
        importance=0.1,
        confidence=0.5,
        risk_level="low",
        created_at=now - timedelta(days=2),
    )

    assert score_attention_signal(urgent, now) > score_attention_signal(low, now)


def test_working_memory_scoring_excludes_expired_unpinned_slot() -> None:
    """Expired unpinned slots are not eligible for attention."""
    now = datetime.now(UTC)
    slot = working_memory_slot(
        expires_at=now - timedelta(seconds=1),
        pinned=False,
    )

    assert score_working_memory_slot(slot, now) == 0.0


def test_working_memory_scoring_keeps_pinned_slot_eligible() -> None:
    """Pinned slots never score below 0.5 unless deleted."""
    now = datetime.now(UTC)
    slot = working_memory_slot(
        priority=0.1,
        confidence=0.1,
        expires_at=now - timedelta(days=1),
        pinned=True,
    )

    assert score_working_memory_slot(slot, now) >= 0.5
