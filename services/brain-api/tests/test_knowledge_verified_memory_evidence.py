from __future__ import annotations

from knowledge_verified_memory_test_helpers import FIXED_TIME, sample_candidate

from aion_brain.knowledge_intelligence.verified_knowledge_evidence import (
    build_verified_knowledge_diagnostics,
    build_verified_knowledge_evidence_bundle,
    build_verified_knowledge_incident,
    build_verified_knowledge_operator_review_item,
)
from aion_brain.knowledge_intelligence.verified_knowledge_integrity import (
    audit_verified_knowledge_candidate,
)


def test_redacted_evidence_and_operator_review_items_create_no_approval() -> None:
    candidate = sample_candidate()
    diagnostics = build_verified_knowledge_diagnostics(
        diagnostics_id="diagnostics-001",
        reason_codes=("verified_candidate_integrity_passed",),
        safe_ids=(candidate.candidate_id,),
    )
    incident = build_verified_knowledge_incident(
        incident_id="incident-001",
        severity_code="info",
        reason_codes=("verified_memory_integrity_passed",),
        candidate_ids=(candidate.candidate_id,),
        created_at=FIXED_TIME,
    )
    bundle = build_verified_knowledge_evidence_bundle(
        evidence_bundle_id="evidence-001",
        candidates=(candidate,),
        integrity_report=audit_verified_knowledge_candidate(candidate),
    )
    review = build_verified_knowledge_operator_review_item(
        review_item_id="review-001",
        candidate=candidate,
        created_at=FIXED_TIME,
    )
    assert diagnostics.redacted is True
    assert incident.redacted is True
    assert bundle.redacted is True
    assert review.candidate_is_not_factual_truth is True
    assert review.approval_created is False
