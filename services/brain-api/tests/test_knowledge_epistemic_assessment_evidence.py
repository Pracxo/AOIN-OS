"""AION-211 diagnostics and operator evidence tests."""

from aion_brain.knowledge_intelligence.epistemic_evidence import (
    diagnostics_for_batch,
    evidence_bundle_for_batch,
)
from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_diagnostics_and_evidence_bundle_are_redacted() -> None:
    batch = assessment_batch()
    diagnostics = diagnostics_for_batch(batch)
    bundle = evidence_bundle_for_batch(batch)
    assert diagnostics.redacted is True
    assert bundle.persistent_assessment_write_enabled is False
    assert bundle.runtime_effect is False
