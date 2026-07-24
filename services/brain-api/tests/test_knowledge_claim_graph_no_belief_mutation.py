from __future__ import annotations

from test_knowledge_claim_graph_helpers import graph_repository

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimGraphResourceUsage,
    evaluate_claim_graph_budget,
)


def test_belief_creation_and_mutation_remain_disabled() -> None:
    repository = graph_repository()
    assert all(record.belief_created is False for record in repository.records())
    assert all(record.belief_mutated is False for record in repository.records())
    decision = evaluate_claim_graph_budget(ClaimGraphResourceUsage(belief_mutations=1))
    assert decision.within_budget is False
