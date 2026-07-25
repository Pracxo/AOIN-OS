"""AION-211 no persistent-write tests."""

from aion_brain.knowledge_intelligence.epistemic_assessment import (
    ControlledEpistemicAssessmentEngine,
)


def test_persistent_assessment_write_is_rejected() -> None:
    decision = ControlledEpistemicAssessmentEngine().reject_persistent_write(1)
    assert decision.within_budget is False
    assert decision.persistent_write_allowed is False
    assert "epistemic_persistent_write_disabled" in decision.reason_codes
