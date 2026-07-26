from __future__ import annotations

from knowledge_verified_memory_test_helpers import (
    FIXED_TIME,
    sample_eligibility_input,
    sample_version,
)

from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgeRevalidationRequest,
    VerifiedKnowledgeRevalidationTrigger,
)
from aion_brain.knowledge_intelligence.verified_knowledge_revalidation import (
    revalidate_verified_knowledge_candidate,
)


def test_explicit_revalidation_preserves_prior_version_and_creates_no_approval() -> None:
    prior = sample_version()
    request = VerifiedKnowledgeRevalidationRequest(
        request_id="revalidation-001",
        candidate_version_id=prior.candidate_version_id,
        triggers=(VerifiedKnowledgeRevalidationTrigger.OPERATOR_REQUESTED,),
        requested_at=FIXED_TIME,
    )
    result = revalidate_verified_knowledge_candidate(
        request=request,
        prior_candidate_version=prior,
        eligibility_input=sample_eligibility_input(),
        created_at=FIXED_TIME,
    )
    assert result.prior_candidate_version.candidate_version_id == prior.candidate_version_id
    assert result.new_candidate_version.version_number == 2
    assert result.approval_created is False
    assert result.persistent_write_applied is False
