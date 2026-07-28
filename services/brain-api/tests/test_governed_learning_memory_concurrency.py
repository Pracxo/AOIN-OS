from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from test_governed_learning_memory_contracts import sample_transaction_context

from aion_brain.contracts import governed_learning_memory as glm


def test_concurrency_budget_is_four_and_parallel_plans_remain_deterministic():
    budget = glm.PromotionResourceBudget()
    exceeded = glm.evaluate_resource_budget(glm.PromotionResourceUsage(concurrency=5))

    with ThreadPoolExecutor(max_workers=budget.maximum_concurrency) as executor:
        results = tuple(
            executor.map(
                lambda index: (
                    sample_transaction_context(
                        transaction_id=f"promotion-transaction-concurrent-{index}",
                    ).result.status
                ),
                range(budget.maximum_concurrency),
            )
        )

    assert budget.maximum_concurrency == 4
    assert exceeded.passed is False
    assert all(status is glm.PromotionTransactionStatus.DRY_RUN_PASSED for status in results)
