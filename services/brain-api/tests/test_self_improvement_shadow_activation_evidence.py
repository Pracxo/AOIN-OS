"""AION-181 activation evidence model tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationAuditEvent,
    ShadowActivationDiagnostics,
    ShadowActivationEvidenceBundle,
    ShadowActivationOperatorReviewItem,
    ShadowActivationProvenanceRecord,
)


def test_audit_provenance_diagnostics_and_review_are_inert(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    audit = ShadowActivationAuditEvent(
        audit_event_id="audit-181",
        activation_candidate_id=ctx["candidate"].activation_candidate_id,
        activation_request_id=ctx["request"].activation_request_id,
        event_type="activation_policy_evaluated",
        decision_outcome="simulation_ready",
        reason_codes=("activation_runtime_disabled",),
        created_at=NOW,
    )
    provenance = ShadowActivationProvenanceRecord(
        provenance_record_id="provenance-181",
        activation_candidate_id=ctx["candidate"].activation_candidate_id,
        activation_request_id=ctx["request"].activation_request_id,
        evidence_fingerprints={"candidate": ctx["candidate"].fingerprint},
        created_at=NOW,
    )
    diagnostics = ShadowActivationDiagnostics(
        diagnostics_id="diagnostics-181",
        activation_candidate_id=ctx["candidate"].activation_candidate_id,
        activation_request_id=ctx["request"].activation_request_id,
        candidate_valid=True,
        request_valid=True,
        approval_valid=True,
        budget_within_limits=True,
        monitoring_passed=True,
        deactivation_required=False,
        created_at=NOW,
    )
    review = ShadowActivationOperatorReviewItem(
        review_item_id="review-181",
        activation_candidate_id=ctx["candidate"].activation_candidate_id,
        activation_request_id=ctx["request"].activation_request_id,
        current_state="review_pending",
        decision_outcome="simulation_passed",
        candidate_validation_summary="candidate valid",
        approval_validation_summary="approval valid",
        budget_summary="budget satisfied",
        monitoring_summary="monitoring passed",
        deactivation_summary="deactivation not required",
        evidence_fingerprints={"candidate": ctx["candidate"].fingerprint},
        reason_codes=("activation_simulation_passed",),
        created_at=NOW,
        expires_at=ctx["candidate"].expires_at,
    )
    bundle = ShadowActivationEvidenceBundle(
        activation_candidate_id=ctx["candidate"].activation_candidate_id,
        activation_request_id=ctx["request"].activation_request_id,
        decision_outcome="simulation_passed",
        audit_events=(audit,),
        provenance=provenance,
        diagnostics=diagnostics,
        operator_review_item=review,
        created_at=NOW,
    )
    assert bundle.shadow_activation_enabled is False
    assert bundle.runtime_effect is False


def test_evidence_rejects_runtime_effects(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    with pytest.raises(ValidationError):
        ShadowActivationDiagnostics(
            diagnostics_id="diagnostics-181",
            activation_candidate_id=ctx["candidate"].activation_candidate_id,
            activation_request_id=ctx["request"].activation_request_id,
            candidate_valid=True,
            request_valid=True,
            approval_valid=True,
            budget_within_limits=True,
            monitoring_passed=True,
            deactivation_required=False,
            shadow_activation_enabled=True,
            created_at=NOW,
        )
