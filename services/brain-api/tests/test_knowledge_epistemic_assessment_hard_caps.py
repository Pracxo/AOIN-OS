"""AION-211 hard-cap tests."""

from decimal import Decimal

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_one_independent_group_hard_cap_is_applied() -> None:
    assessment = assessment_batch().assessments[0]
    cap_ids = {cap.cap_id for cap in assessment.hard_caps}
    assert "one_independent_evidence_group" in cap_ids
    assert assessment.confidence <= Decimal("0.400000")
