from __future__ import annotations

from decimal import Decimal

from knowledge_verified_memory_test_helpers import sample_eligibility_input

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeEligibilityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    evaluate_verified_knowledge_candidate_eligibility,
)


def test_candidate_confidence_cap_is_minimum_upstream_cap() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(sample_eligibility_input())
    assert decision.candidate_confidence_cap == Decimal("0.870000")


def test_low_confidence_blocks_review_eligibility() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(required_report_confidence_caps=(Decimal("0.700000"),))
    )
    assert decision.status is VerifiedKnowledgeEligibilityStatus.INELIGIBLE_LOW_CONFIDENCE
