"""AION-211 integrity audit tests."""

from aion_brain.knowledge_intelligence.epistemic_integrity import (
    audit_epistemic_assessment_batch,
)
from tests.test_knowledge_claim_graph_helpers import NOW
from tests.test_knowledge_epistemic_assessment_helpers import assessment_batch


def test_integrity_audit_passes_for_valid_batch() -> None:
    report = audit_epistemic_assessment_batch(assessment_batch(), audit_timestamp=NOW)
    assert report.status == "passed"
    assert report.validated_assessment_count == 1
