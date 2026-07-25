"""AION-211 assessment batch tests."""

from aion_brain.contracts.knowledge_epistemic_assessment import EpistemicAssessmentOutcome
from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_assessment_batch_is_read_only_and_ordered() -> None:
    batch = assessment_batch()
    assert batch.assessment_count == 1
    assert batch.assessments[0].claim_id == batch.request.claim_ids[0]
    assert batch.outcome in {
        EpistemicAssessmentOutcome.COMPLETED,
        EpistemicAssessmentOutcome.COMPLETED_WITH_ABSTENTION,
    }
    assert batch.persistent_write_applied is False
