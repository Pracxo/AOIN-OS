from __future__ import annotations

from aion_brain.contracts import governed_learning_memory as glm


def test_resource_budget_allows_only_authorized_local_planning_limits():
    budget = glm.PromotionResourceBudget()
    passing = glm.evaluate_resource_budget(glm.PromotionResourceUsage(candidates=100))
    exceeded = glm.evaluate_resource_budget(glm.PromotionResourceUsage(candidates=101))

    assert budget.maximum_fixture_bytes == 4_194_304
    assert budget.maximum_concurrency == 4
    assert budget.maximum_persistent_knowledge_writes == 0
    assert passing.passed is True
    assert exceeded.passed is False
    assert "promotion_resource_budget_exceeded" in exceeded.reason_codes
