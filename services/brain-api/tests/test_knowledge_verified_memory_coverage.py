from __future__ import annotations

from decimal import Decimal

from knowledge_verified_memory_test_helpers import sample_eligibility_input

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeEligibilityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    evaluate_verified_knowledge_candidate_eligibility,
)


def test_incomplete_provenance_blocks_candidate() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(provenance_completeness=Decimal("0.900000"))
    )
    assert decision.status is (
        VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INCOMPLETE_PROVENANCE
    )


def test_incomplete_citation_coverage_blocks_candidate() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(citation_coverage=Decimal("0.900000"))
    )
    assert decision.status is (
        VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INCOMPLETE_CITATIONS
    )
