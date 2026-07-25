"""AION-211 no belief mutation tests."""

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_assessment_does_not_create_or_mutate_belief() -> None:
    assessment = assessment_batch().assessments[0]
    assert assessment.belief_created is False
    assert assessment.belief_mutated is False
