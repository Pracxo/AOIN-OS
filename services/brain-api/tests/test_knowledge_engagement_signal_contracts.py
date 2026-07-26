from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_signal

from aion_brain.contracts.knowledge_verified_memory import EngagementSignalKind
from aion_brain.knowledge_intelligence.engagement_signal_policy import (
    build_engagement_signal_batch,
)


def test_engagement_signal_batch_is_bounded_and_ordered() -> None:
    second = sample_signal(
        signal_id="signal-002",
        signal_kind=EngagementSignalKind.RETRIEVAL_FAILED,
    )
    first = sample_signal(signal_id="signal-001")
    batch = build_engagement_signal_batch(batch_id="signals-001", signals=(second, first))
    assert batch.signal_count == 2
    assert tuple(signal.signal_id for signal in batch.signals) == ("signal-001", "signal-002")
    assert batch.factual_effect is False
