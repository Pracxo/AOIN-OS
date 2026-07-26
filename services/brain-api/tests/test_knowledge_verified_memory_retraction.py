from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_eligibility_input, sample_version

from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgeEligibilityStatus,
    VerifiedKnowledgeLifecycleStatus,
)
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    evaluate_verified_knowledge_candidate_eligibility,
)
from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
    retract_candidate_version,
)


def test_retraction_blocks_candidate() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(retraction_applicable=True)
    )
    assert decision.status is VerifiedKnowledgeEligibilityStatus.INELIGIBLE_RETRACTED


def test_retraction_records_new_version_without_deleting_history() -> None:
    retracted = retract_candidate_version(sample_version())
    assert retracted.version_number == 2
    assert retracted.candidate.lifecycle_status is VerifiedKnowledgeLifecycleStatus.RETRACTED
