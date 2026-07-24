from __future__ import annotations

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimGraphResourceUsage,
    evaluate_claim_graph_budget,
)


def test_automatic_claim_extraction_is_disabled_by_budget() -> None:
    decision = evaluate_claim_graph_budget(ClaimGraphResourceUsage(automatic_claim_extractions=1))
    assert decision.within_budget is False
    assert "claim_graph_automatic_extraction_blocked" in decision.reason_codes
