from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_eligibility_input

from aion_brain.contracts.knowledge_epistemic_assessment import FreshnessStatus
from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeEligibilityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    evaluate_verified_knowledge_candidate_eligibility,
)


def test_stale_evidence_blocks_candidate() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(freshness_status=FreshnessStatus.STALE)
    )
    assert decision.status is VerifiedKnowledgeEligibilityStatus.INELIGIBLE_STALE
