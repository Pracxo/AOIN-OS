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
    supersede_candidate_version,
)


def test_supersession_without_current_evidence_blocks_candidate() -> None:
    decision = evaluate_verified_knowledge_candidate_eligibility(
        sample_eligibility_input(
            supersession_applicable=True,
            current_evidence_after_supersession=False,
        )
    )
    assert decision.status is VerifiedKnowledgeEligibilityStatus.INELIGIBLE_SUPERSEDED


def test_supersession_records_new_version_without_deleting_history() -> None:
    superseded = supersede_candidate_version(sample_version())
    assert superseded.version_number == 2
    assert superseded.candidate.lifecycle_status is VerifiedKnowledgeLifecycleStatus.SUPERSEDED
