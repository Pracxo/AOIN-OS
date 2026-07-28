from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_transaction_status_blocks_when_required_approval_evidence_is_insufficient():
    context = sample_transaction_context(
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        risk_class=glm.PromotionRiskClass.CRITICAL,
        approval_pairs=1,
    )

    assert context.result.status is glm.PromotionTransactionStatus.BLOCKED
    assert context.result.ready_for_future_persistence_review is False
