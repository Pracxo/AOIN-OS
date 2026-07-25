"""AION-211 contradiction evaluation tests."""

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_structural_conflict_candidate_is_preserved_unresolved() -> None:
    batch = assessment_batch()
    assessment = batch.assessments[0]
    assert assessment.structural_conflict_candidate_ids
    assert assessment.contradiction_resolved is False
    assert "epistemic_structural_conflict_material" in assessment.reason_codes
