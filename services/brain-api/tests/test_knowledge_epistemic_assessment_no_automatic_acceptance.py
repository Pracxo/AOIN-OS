"""AION-211 no automatic acceptance tests."""

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_assessment_does_not_accept_or_reject_claims() -> None:
    assessment = assessment_batch().assessments[0]
    assert assessment.claim_accepted is False
    assert assessment.claim_rejected is False
