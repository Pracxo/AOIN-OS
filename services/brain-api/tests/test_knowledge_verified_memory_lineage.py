from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_lineage

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeIntegrityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_integrity import (
    audit_integrated_knowledge_lineage,
)
from aion_brain.knowledge_intelligence.verified_knowledge_lineage import (
    audit_integrated_knowledge_lineage as audit_lineage_public_api,
)


def test_integrated_lineage_preserves_all_upstream_reference_planes() -> None:
    lineage = sample_lineage()
    assert lineage.lineage_reference_count == 11
    assert lineage.read_only is True
    assert lineage.redacted is True
    assert lineage.runtime_effect is False
    assert lineage.tool_verification_session_ids == ("tool-session-001",)
    assert lineage.attestation_chain_head_fingerprints


def test_integrated_lineage_audit_passes_redacted() -> None:
    report = audit_integrated_knowledge_lineage(sample_lineage())
    assert report.status is VerifiedKnowledgeIntegrityStatus.PASSED
    assert report.redacted is True


def test_public_lineage_audit_preserves_integrity_report_fingerprint() -> None:
    report = audit_lineage_public_api(sample_lineage())
    assert report.status is VerifiedKnowledgeIntegrityStatus.PASSED
    assert report.redacted is True
    assert report.report_fingerprint
