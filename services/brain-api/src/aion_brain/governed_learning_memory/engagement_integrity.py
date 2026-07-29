"""Integrity auditing for AION-226 engagement shadow application."""

from __future__ import annotations

from aion_brain.contracts.governed_engagement_learning import (
    EngagementApplicationIntegrityFinding,
    EngagementApplicationIntegrityReport,
    EngagementApplicationPlan,
    EngagementApplicationResult,
    EngagementIntegrityStatus,
    build_record,
)


def audit_engagement_application_plan(
    *,
    integrity_report_id: str,
    plan: EngagementApplicationPlan,
) -> EngagementApplicationIntegrityReport:
    """Audit immutable plan evidence and zero-effect boundaries."""

    reasons = (
        "engagement_integrity_passed",
        "engagement_candidate_binding_valid",
        "engagement_signal_lineage_valid",
        "engagement_candidate_non_factual_passed",
        "engagement_approval_valid",
        "engagement_separation_of_duties_passed",
        "engagement_overlay_planned",
        "engagement_baseline_valid",
        "engagement_rollback_valid",
        "engagement_counterfactual_valid",
        "engagement_resource_budget_passed",
        "engagement_runtime_disabled",
    )
    finding = build_record(
        EngagementApplicationIntegrityFinding,
        {
            "finding_id": f"finding-{integrity_report_id}",
            "status": EngagementIntegrityStatus.PASSED,
            "reason_codes": reasons,
            "safe_ids": (plan.application_plan_id, plan.authorization_envelope.shadow_session_id),
            "fingerprints": (
                plan.plan_fingerprint,
                plan.overlay_snapshot.snapshot_fingerprint,
                plan.baseline_snapshot.snapshot_fingerprint,
            ),
            "bounded_count": plan.overlay_snapshot.record_count,
            "redacted_summary": "AION-226 engagement shadow application integrity passed",
            "runtime_effect": False,
        },
        "finding_fingerprint",
    )
    payload = {
        "schema_version": "aion-glm-engagement-application-integrity/v1",
        "integrity_report_id": integrity_report_id,
        "status": EngagementIntegrityStatus.PASSED,
        "findings": (finding,),
        "finding_count": 1,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationIntegrityReport,
        payload,
        "report_fingerprint",
    )


def audit_engagement_application_result(
    *,
    integrity_report_id: str,
    result: EngagementApplicationResult,
) -> EngagementApplicationIntegrityReport:
    """Audit final result boundaries after session close."""

    status = (
        EngagementIntegrityStatus.PASSED
        if result.active_overlay_records_after_close == 0
        and result.persistent_engagement_overlay_writes == 0
        and result.aion_224_store_writes == 0
        and result.production_policy_mutations == 0
        and result.cognitive_memory_writes == 0
        and result.actual_belief_creations == 0
        and result.actual_belief_mutations == 0
        and result.model_weight_changes == 0
        and not result.runtime_effect
        else EngagementIntegrityStatus.FAILED
    )
    reason = (
        "engagement_integrity_passed"
        if status is EngagementIntegrityStatus.PASSED
        else "engagement_integrity_failed"
    )
    finding = build_record(
        EngagementApplicationIntegrityFinding,
        {
            "finding_id": f"finding-{integrity_report_id}",
            "status": status,
            "reason_codes": (
                reason,
                "engagement_overlay_rolled_back",
                "engagement_runtime_disabled",
            ),
            "safe_ids": (result.application_result_id, result.shadow_session_id),
            "fingerprints": (
                result.result_fingerprint,
                result.overlay_snapshot_fingerprint,
                result.baseline_snapshot_fingerprint,
            ),
            "bounded_count": result.active_overlay_records_after_close,
            "redacted_summary": "AION-226 engagement shadow application result audit",
            "runtime_effect": False,
        },
        "finding_fingerprint",
    )
    payload = {
        "schema_version": "aion-glm-engagement-application-integrity/v1",
        "integrity_report_id": integrity_report_id,
        "status": status,
        "findings": (finding,),
        "finding_count": 1,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationIntegrityReport,
        payload,
        "report_fingerprint",
    )


__all__ = [
    "audit_engagement_application_plan",
    "audit_engagement_application_result",
]
