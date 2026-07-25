"""AION-211 no absolute truth tests."""

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_assessment_never_claims_absolute_truth() -> None:
    assessment = assessment_batch().assessments[0]
    assert assessment.absolute_truth_claimed is False
    assert "epistemic_absolute_truth_oracle_blocked" not in assessment.reason_codes
