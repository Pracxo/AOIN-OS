from __future__ import annotations

from test_knowledge_claim_graph_helpers import claim

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimGraphResourceUsage,
    evaluate_claim_graph_budget,
)


def test_claims_never_assign_truth_values() -> None:
    item = claim()
    assert item.truth_value_assigned is False
    decision = evaluate_claim_graph_budget(ClaimGraphResourceUsage(truth_decisions=1))
    assert decision.within_budget is False
    assert "claim_graph_truth_decision_blocked" in decision.reason_codes
