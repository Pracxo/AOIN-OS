from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context


def test_transaction_never_applies_automatic_promotion():
    context = sample_transaction_context()

    assert context.result.actual_knowledge_promotion_applied is False
    assert context.result.automatic_promotions == 0
    assert all(
        item.operator_review_required is True for item in context.result.operator_review_items
    )
