"""AION-211 status tests."""

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_status_describes_evidence_posture_only() -> None:
    assessment = assessment_batch().assessments[0]
    assert assessment.status == "supported"
    assert assessment.claim_accepted is False
    assert assessment.claim_rejected is False
