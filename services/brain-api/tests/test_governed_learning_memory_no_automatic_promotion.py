from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_automatic_candidate_approval_and_promotion_remain_disabled() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")
    request = load_json("examples/governed-learning-memory/knowledge-promotion-request.json")
    transaction = load_json("examples/governed-learning-memory/promotion-transaction-plan.json")

    assert auth["prohibited_capabilities"]["automatic_candidate_approval_enabled"] is False
    assert auth["prohibited_capabilities"]["automatic_knowledge_promotion_enabled"] is False
    assert request["approval_required"] is True
    assert request["automatic_knowledge_promotion_enabled"] is False
    assert transaction["dry_run_promotion_transaction_approved"] is True
    assert transaction["persistent_knowledge_write_enabled"] is False
    assert auth["resource_limits"]["maximum_automatic_knowledge_promotions"] == 0
    assert auth["resource_limits"]["maximum_automatic_candidate_approvals"] == 0
