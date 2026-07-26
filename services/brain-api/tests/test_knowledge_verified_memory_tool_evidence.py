from __future__ import annotations

from decimal import Decimal

from knowledge_verified_memory_test_helpers import sample_eligibility_input

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeEligibilityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    evaluate_verified_knowledge_candidate_eligibility,
)


def test_tool_evidence_can_reduce_but_not_increase_confidence() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(tool_evidence_confidence_caps=(Decimal("0.860000"),))
    )
    assert decision.candidate_confidence_cap == Decimal("0.860000")


def test_actual_tool_execution_blocks_candidate_integrity() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(actual_tool_executed=True)
    )
    assert decision.status is VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INTEGRITY_FAILURE
