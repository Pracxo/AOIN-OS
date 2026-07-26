from __future__ import annotations

from aion_brain.contracts.knowledge_verified_memory import (
    AUTHORIZATION_TRANSACTION_ID,
    MAXIMUM_AUTOMATIC_KNOWLEDGE_PROMOTIONS,
    MAXIMUM_COGNITIVE_MEMORY_WRITES,
    MAXIMUM_ENGAGEMENT_CONFIDENCE_EFFECTS,
    MAXIMUM_ENGAGEMENT_FACT_PROMOTIONS,
    MAXIMUM_PERSISTENT_VERIFIED_KNOWLEDGE_WRITE_BATCH,
    VERIFIED_KNOWLEDGE_MEMORY_STATE,
    VerifiedKnowledgeResourceUsage,
    evaluate_verified_knowledge_budget,
)


def test_contract_constants_preserve_aion_216_authorization_boundary() -> None:
    assert AUTHORIZATION_TRANSACTION_ID == "AION-216-KI-0007"
    assert VERIFIED_KNOWLEDGE_MEMORY_STATE.endswith("persistent_write_disabled")
    assert MAXIMUM_PERSISTENT_VERIFIED_KNOWLEDGE_WRITE_BATCH == 0
    assert MAXIMUM_AUTOMATIC_KNOWLEDGE_PROMOTIONS == 0
    assert MAXIMUM_COGNITIVE_MEMORY_WRITES == 0
    assert MAXIMUM_ENGAGEMENT_FACT_PROMOTIONS == 0
    assert MAXIMUM_ENGAGEMENT_CONFIDENCE_EFFECTS == 0


def test_budget_decision_fails_closed_for_forbidden_counters() -> None:
    decision = evaluate_verified_knowledge_budget(
        VerifiedKnowledgeResourceUsage(persistent_verified_knowledge_write_batch=1)
    )
    assert decision.within_budget is False
    assert decision.failed_counters == ("persistent_verified_knowledge_write_batch",)
