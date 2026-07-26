from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_candidate

from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgeCandidateKind,
    VerifiedKnowledgeEligibilityStatus,
)


def test_refutation_candidate_uses_opposition_count_without_truth_assignment() -> None:
    candidate = sample_candidate(
        candidate_kind=VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE,
        suffix="002",
    )
    assert candidate.candidate_kind is VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE
    assert candidate.independent_opposition_count == 3
    assert candidate.eligibility_decision.status is (
        VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
    )
    assert candidate.belief_mutated is False
