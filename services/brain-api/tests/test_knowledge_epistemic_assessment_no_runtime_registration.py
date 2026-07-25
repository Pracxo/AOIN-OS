"""AION-211 no runtime registration tests."""

from pathlib import Path

from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_epistemic_assessment_has_no_runtime_registration_file() -> None:
    brain_api = Path(__file__).resolve().parents[1]
    assert not (brain_api / "src/aion_brain/knowledge_intelligence/epistemic_runtime.py").exists()
    assert assessment_batch().runtime_effect is False
