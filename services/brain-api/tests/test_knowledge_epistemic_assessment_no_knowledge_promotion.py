"""AION-211 no knowledge promotion tests."""

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_assessment_does_not_promote_knowledge() -> None:
    assert assessment_batch().assessments[0].knowledge_promoted is False
