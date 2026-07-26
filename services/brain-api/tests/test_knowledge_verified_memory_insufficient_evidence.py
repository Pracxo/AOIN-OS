from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_eligibility_input

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeEligibilityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    evaluate_verified_knowledge_candidate_eligibility,
)


def test_insufficient_independent_support_is_ineligible() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(independent_support_count=2)
    )
    assert decision.status is VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INSUFFICIENT_EVIDENCE
