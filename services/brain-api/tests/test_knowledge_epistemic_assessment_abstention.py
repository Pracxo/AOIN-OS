"""AION-211 abstention tests."""

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_explicit_abstention_is_required_when_hard_capped() -> None:
    assessment = assessment_batch().assessments[0]
    assert assessment.explicit_abstention is True
    assert "epistemic_explicit_abstention_required" in assessment.reason_codes
