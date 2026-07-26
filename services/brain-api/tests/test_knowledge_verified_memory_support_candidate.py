from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate

from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgeCandidateKind,
    VerifiedKnowledgeEligibilityStatus,
)


def test_support_candidate_is_reviewable_evidence_only() -> None:
    candidate = sample_candidate(
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
    )
    assert candidate.candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
    assert candidate.eligibility_decision.status is (
        VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
    )
    assert candidate.verified_knowledge_created is False
