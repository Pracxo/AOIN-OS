from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_eligibility_input

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeEligibilityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    evaluate_verified_knowledge_candidate_eligibility,
)


def test_eligible_candidate_requires_operator_review_not_promotion() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(sample_eligibility_input())
    assert decision.status is VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
    assert decision.operator_review_required is True
    assert decision.automatic_promotion is False
    assert decision.verified_knowledge_created is False
