from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_signal_batch

from aion_brain.knowledge_intelligence.engagement_learning_candidates import (
    build_engagement_learning_candidates,
)


def test_engagement_learning_candidates_do_not_apply_policy_or_train_models() -> None:
    batch = build_engagement_learning_candidates(
        batch_id="learning-001",
        signal_batch=sample_signal_batch(),
    )
    candidate = batch.candidates[0]
    assert candidate.automatic_application is False
    assert candidate.model_weight_effect is False
    assert batch.automatic_application is False
