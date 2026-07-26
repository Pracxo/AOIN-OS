from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_signal_batch

from aion_brain.knowledge_intelligence.engagement_learning_candidates import (
    build_engagement_learning_candidates,
    version_engagement_learning_candidate,
)


def test_engagement_learning_candidate_versioning_is_immutable() -> None:
    batch = build_engagement_learning_candidates(
        batch_id="learning-001",
        signal_batch=sample_signal_batch(),
    )
    first = batch.candidates[0]
    second = version_engagement_learning_candidate(first)
    assert second.candidate_version == 2
    assert second.supersedes_candidate_id == first.learning_candidate_id
    assert second.automatic_application is False
