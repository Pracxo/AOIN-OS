from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_repository

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimGraphResourceUsage,
    evaluate_claim_graph_budget,
)


def test_knowledge_promotion_remains_disabled() -> None:
    repository = graph_repository()
    assert all(record.knowledge_promoted is False for record in repository.records())
    decision = evaluate_claim_graph_budget(ClaimGraphResourceUsage(knowledge_promotions=1))
    assert decision.within_budget is False
