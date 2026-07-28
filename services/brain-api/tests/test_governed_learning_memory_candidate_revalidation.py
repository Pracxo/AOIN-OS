from __future__ import annotations

from datetime import timedelta

from knowledge_verified_memory_test_helpers import FIXED_TIME, fp
from test_governed_learning_memory_contracts import sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_candidate_revalidation_uses_existing_candidate_state_only():
    context = sample_transaction_context()
    binding = context.planner.bind_candidates(
        context.request,
        (context.candidate,),
        memory_snapshot_id="memory-snapshot-revalidation",
        memory_snapshot_fingerprint=fp("memory-snapshot-revalidation"),
    )[0]
    snapshot = glm.revalidate_promotion_candidate(
        binding,
        revalidated_at=FIXED_TIME + timedelta(minutes=2),
        valid_until=FIXED_TIME + timedelta(hours=1),
    )

    assert snapshot.disposition is glm.PromotionCandidateDisposition.ELIGIBLE_FOR_DRY_RUN
    assert snapshot.automatic_promotion is False
    assert snapshot.persistent_write_applied is False
    assert snapshot.cognitive_memory_written is False
    assert snapshot.belief_mutated is False
