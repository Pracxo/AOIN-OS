from __future__ import annotations

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimGraphResourceUsage,
    evaluate_claim_graph_budget,
)


def test_exact_zero_write_budget_accepts_valid_usage_and_blocks_forbidden_counters() -> None:
    ok = evaluate_claim_graph_budget(ClaimGraphResourceUsage(claim_nodes=1000))
    assert ok.within_budget is True
    assert ok.budget.maximum_graph_write_batch == 0
    too_many = evaluate_claim_graph_budget(ClaimGraphResourceUsage(claim_nodes=1001))
    assert too_many.within_budget is False
    persistent = evaluate_claim_graph_budget(ClaimGraphResourceUsage(graph_write_batch=1))
    assert persistent.within_budget is False
    assert "claim_graph_persistent_write_disabled" in persistent.reason_codes
    blocked = evaluate_claim_graph_budget(
        ClaimGraphResourceUsage(
            automatic_claim_extractions=1,
            truth_decisions=1,
            confidence_calculations=1,
            knowledge_promotions=1,
            belief_mutations=1,
            network_calls=1,
            git_operations=1,
        )
    )
    assert blocked.within_budget is False
