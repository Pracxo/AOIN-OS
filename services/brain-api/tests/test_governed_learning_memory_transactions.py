from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_transaction_result_is_ready_for_future_review_but_not_authorized():
    context = sample_transaction_context()

    assert context.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
    assert context.result.ready_for_future_persistence_review is True
    assert context.result.future_persistence_authorized is False
    assert context.result.actual_knowledge_promotion_applied is False
