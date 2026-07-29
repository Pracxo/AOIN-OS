"""Existing approval evidence projection for engagement shadow application."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.governed_engagement_learning import (
    EngagementApplicationApprovalBundle,
    EngagementApplicationApprovalEvidence,
    EngagementApplicationRiskAssessment,
    EngagementApplicationRiskClass,
    build_record,
    engagement_fingerprint,
    target_spec_for_candidate_kind,
    utc_now,
)
from aion_brain.contracts.knowledge_verified_memory import EngagementLearningCandidateKind

REQUIRED_ACTION_TYPE = "governed_learning_memory.apply_engagement_shadow_overlay"
REQUIRED_RESOURCE_TYPE = "engagement_learning_candidate"
REQUIRED_APPROVAL_SCOPE = "governed-learning-memory:engagement-shadow-application"


def classify_engagement_application_risk(
    *,
    risk_assessment_id: str,
    candidate_id: str,
    candidate_fingerprint: str,
    candidate_kind: EngagementLearningCandidateKind,
    assessed_at: datetime | None = None,
) -> EngagementApplicationRiskAssessment:
    """Classify risk from the fixed AION-226 target registry."""

    spec = target_spec_for_candidate_kind(candidate_kind)
    required = 1 if spec.risk_class is EngagementApplicationRiskClass.LOW else 2
    reason = (
        "engagement_risk_low"
        if spec.risk_class is EngagementApplicationRiskClass.LOW
        else "engagement_risk_elevated"
    )
    payload = {
        "schema_version": "aion-glm-engagement-application-risk/v1",
        "risk_assessment_id": risk_assessment_id,
        "candidate_id": candidate_id,
        "candidate_fingerprint": candidate_fingerprint,
        "candidate_kind": candidate_kind,
        "target_component_code": spec.target_component_code,
        "target_policy_code": spec.target_policy_code,
        "risk_class": spec.risk_class,
        "required_independent_approvers": required,
        "risk_reason_codes": (reason,),
        "assessed_at": assessed_at or utc_now(),
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationRiskAssessment,
        payload,
        "assessment_fingerprint",
    )


def _payload_value(request: ApprovalRequest, key: str) -> object:
    return request.payload.get(key)


def project_existing_engagement_application_approval(
    *,
    approval_request: ApprovalRequest,
    approval_decision: ApprovalDecision,
    candidate_id: str,
    candidate_fingerprint: str,
    candidate_version: int,
    signal_fingerprints: tuple[str, ...],
    adaptation_identity_id: str,
    adaptation_version: int,
    target_component_code: str,
    target_policy_code: str,
    overlay_fingerprint: str,
    baseline_snapshot_fingerprint: str,
    fixture_fingerprint: str,
    rollback_plan_fingerprint: str,
    overlay_expires_at: datetime,
    requested_at: datetime | None = None,
    decided_at: datetime | None = None,
    approval_expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> EngagementApplicationApprovalEvidence:
    """Project existing operator approval records without creating approval state."""

    if approval_request.approval_request_id != approval_decision.approval_request_id:
        raise ValueError("approval request and decision id mismatch")
    if approval_request.status != "approved":
        raise ValueError("approval request must already be approved")
    if approval_decision.decision != "approve":
        raise ValueError("approval decision must already approve")
    if approval_request.action_type != REQUIRED_ACTION_TYPE:
        raise ValueError("approval action type mismatch")
    if approval_request.resource_type != REQUIRED_RESOURCE_TYPE:
        raise ValueError("approval resource type mismatch")
    if REQUIRED_APPROVAL_SCOPE not in approval_request.approval_scope:
        raise ValueError("approval scope mismatch")
    if approval_request.resource_id != candidate_id:
        raise ValueError("approval resource id mismatch")

    bindings = {
        "candidate_id": candidate_id,
        "candidate_fingerprint": candidate_fingerprint,
        "candidate_version": candidate_version,
        "signal_fingerprints": signal_fingerprints,
        "adaptation_identity_id": adaptation_identity_id,
        "adaptation_version": adaptation_version,
        "target_component_code": target_component_code,
        "target_policy_code": target_policy_code,
        "overlay_fingerprint": overlay_fingerprint,
        "baseline_snapshot_fingerprint": baseline_snapshot_fingerprint,
        "fixture_fingerprint": fixture_fingerprint,
        "rollback_plan_fingerprint": rollback_plan_fingerprint,
        "overlay_expires_at": overlay_expires_at.isoformat(),
    }
    for key, value in bindings.items():
        if _payload_value(approval_request, key) != value:
            raise ValueError(f"approval binding mismatch: {key}")

    req_time = requested_at or approval_request.created_at or utc_now()
    dec_time = decided_at or approval_decision.created_at or utc_now()
    expires = approval_expires_at or approval_request.expires_at
    if expires is None:
        raise ValueError("approval expiry is required")
    if expires <= dec_time:
        raise ValueError("approval is expired")
    requester = engagement_fingerprint(
        {
            "requester": approval_request.requested_by
            or approval_request.actor_id
            or "unknown-requester"
        }
    )
    approver = engagement_fingerprint(
        {"approver": approval_decision.decided_by or "unknown-approver"}
    )
    payload = {
        "schema_version": "aion-glm-engagement-application-approval-evidence/v1",
        "approval_evidence_id": f"approval-evidence-{approval_decision.approval_decision_id}",
        "approval_request_id": approval_request.approval_request_id,
        "approval_decision_id": approval_decision.approval_decision_id,
        "approval_request_fingerprint": engagement_fingerprint(
            approval_request.model_dump(mode="python")
        ),
        "approval_decision_fingerprint": engagement_fingerprint(
            approval_decision.model_dump(mode="python")
        ),
        "requester_identity_fingerprint": requester,
        "approver_identity_fingerprint": approver,
        "action_type": approval_request.action_type,
        "resource_type": approval_request.resource_type,
        "resource_id": approval_request.resource_id or candidate_id,
        "approval_scope": REQUIRED_APPROVAL_SCOPE,
        "decision": "approve",
        "request_status": "approved",
        "candidate_id": candidate_id,
        "candidate_fingerprint": candidate_fingerprint,
        "candidate_version": candidate_version,
        "signal_fingerprints": signal_fingerprints,
        "adaptation_identity_id": adaptation_identity_id,
        "adaptation_version": adaptation_version,
        "target_component_code": target_component_code,
        "target_policy_code": target_policy_code,
        "overlay_fingerprint": overlay_fingerprint,
        "baseline_snapshot_fingerprint": baseline_snapshot_fingerprint,
        "fixture_fingerprint": fixture_fingerprint,
        "rollback_plan_fingerprint": rollback_plan_fingerprint,
        "overlay_expires_at": overlay_expires_at,
        "requested_at": req_time,
        "decided_at": dec_time,
        "approval_expires_at": expires,
        "revoked_at": revoked_at,
        "evidence_origin": "operator_supplied_existing_approval",
        "approval_creation_performed_by_aion226": False,
        "approval_decision_performed_by_aion226": False,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationApprovalEvidence,
        payload,
        "evidence_fingerprint",
    )


def build_approval_bundle(
    *,
    bundle_id: str,
    risk_assessment: EngagementApplicationRiskAssessment,
    evidence_records: tuple[EngagementApplicationApprovalEvidence, ...],
) -> EngagementApplicationApprovalBundle:
    """Build deterministic approval bundle and enforce separation of duties."""

    approvers = tuple(
        sorted({item.approver_identity_fingerprint for item in evidence_records})
    )
    passed = len(approvers) >= risk_assessment.required_independent_approvers
    reasons = [
        "engagement_approval_valid" if passed else "engagement_approval_insufficient_approvers",
        "engagement_separation_of_duties_passed"
        if passed
        else "engagement_separation_of_duties_failed",
    ]
    payload = {
        "schema_version": "aion-glm-engagement-application-approval-bundle/v1",
        "bundle_id": bundle_id,
        "risk_class": risk_assessment.risk_class,
        "evidence_records": tuple(
            sorted(evidence_records, key=lambda item: item.approval_evidence_id)
        ),
        "independent_approver_fingerprints": approvers,
        "independent_approver_count": len(approvers),
        "required_independent_approvers": risk_assessment.required_independent_approvers,
        "separation_of_duties_passed": passed,
        "approval_status": "approved" if passed else "blocked",
        "reason_codes": tuple(reasons),
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationApprovalBundle,
        payload,
        "bundle_fingerprint",
    )


__all__ = [
    "REQUIRED_ACTION_TYPE",
    "REQUIRED_APPROVAL_SCOPE",
    "REQUIRED_RESOURCE_TYPE",
    "build_approval_bundle",
    "classify_engagement_application_risk",
    "project_existing_engagement_application_approval",
]
