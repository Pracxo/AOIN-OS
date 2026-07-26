from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate, sample_signal


def test_engagement_metadata_does_not_change_candidate_confidence() -> None:
    before = sample_candidate(engagement_signal_count=0)
    after = sample_candidate(engagement_signal_count=1)
    signal = sample_signal()
    assert signal.confidence_effect is False
    assert before.candidate_confidence_cap == after.candidate_confidence_cap
