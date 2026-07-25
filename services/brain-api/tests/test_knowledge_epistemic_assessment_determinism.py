"""AION-211 determinism tests."""

from aion_brain.knowledge_intelligence.epistemic_assessment import stable_assessment_json
from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_assessment_output_is_deterministic() -> None:
    assert stable_assessment_json(assessment_batch()) == stable_assessment_json(assessment_batch())
