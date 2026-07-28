from __future__ import annotations

from test_governed_learning_memory_contracts import sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_queries_are_exact_read_only_journal_filters():
    context = sample_transaction_context()
    result = context.journal.query(
        glm.PromotionTransactionQuery(
            transaction_status=glm.PromotionTransactionStatus.DRY_RUN_PASSED,
            ready_for_future_persistence_review=True,
        )
    )

    assert result.result_count == 1
    assert result.exact_match_only is True
    assert result.semantic_search_used is False
    assert result.results[0].transaction_id == context.result.transaction_id
