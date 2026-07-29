"""Redacted evidence and operator-review items for engagement shadow application."""

from __future__ import annotations

from aion_brain.contracts.governed_engagement_learning import (
    EngagementApplicationDiagnostics,
    EngagementApplicationEvidenceBundle,
    EngagementApplicationIncident,
    EngagementApplicationOperatorReviewItem,
    EngagementCounterfactualRecommendation,
    EngagementIntegrityStatus,
    build_record,
)


def build_operator_review_item(
    *,
    review_item_id: str,
    candidate_id: str,
    recommendation: EngagementCounterfactualRecommendation,
    reason_codes: tuple[str, ...],
) -> EngagementApplicationOperatorReviewItem:
    payload = {
        "review_item_id": review_item_id,
        "candidate_id": candidate_id,
        "recommendation": recommendation,
        "reason_codes": reason_codes,
        "operator_review_required": True,
        "candidate_is_non_factual": True,
        "operator_approval_is_not_factual_proof": True,
        "shadow_application_is_not_production_application": True,
        "metric_improvement_is_not_factual_validation": True,
        "overlay_is_in_memory_only": True,
        "persistent_overlay_authorized": False,
        "production_policy_mutation_authorized": False,
        "knowledge_confidence_change_authorized": False,
        "source_independence_change_authorized": False,
        "cognitive_memory_write_authorized": False,
        "belief_mutation_authorized": False,
        "automatic_application_authorized": False,
        "model_training_authorized": False,
        "approval_created": False,
        "new_implementation_authorization_created": False,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationOperatorReviewItem,
        payload,
        "review_item_fingerprint",
    )


def build_evidence_bundle(
    *,
    evidence_bundle_id: str,
    bounded_counts: dict[str, int],
    operator_review_items: tuple[EngagementApplicationOperatorReviewItem, ...],
    incidents: tuple[EngagementApplicationIncident, ...] = (),
) -> EngagementApplicationEvidenceBundle:
    diagnostics = build_record(
        EngagementApplicationDiagnostics,
        {
            "diagnostics_id": f"diagnostics-{evidence_bundle_id}",
            "reason_codes": (
                "engagement_integrity_passed",
                "engagement_runtime_disabled",
                "engagement_overlay_rolled_back",
            ),
            "bounded_counts": bounded_counts,
            "redacted": True,
            "runtime_effect": False,
        },
        "diagnostics_fingerprint",
    )
    payload = {
        "schema_version": "aion-glm-engagement-application-evidence/v1",
        "evidence_bundle_id": evidence_bundle_id,
        "diagnostics": diagnostics,
        "incidents": incidents,
        "operator_review_items": operator_review_items,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationEvidenceBundle,
        payload,
        "evidence_bundle_fingerprint",
    )


def build_blocked_incident(
    *,
    incident_id: str,
    reason_codes: tuple[str, ...],
    safe_ids: tuple[str, ...],
) -> EngagementApplicationIncident:
    return build_record(
        EngagementApplicationIncident,
        {
            "incident_id": incident_id,
            "status": EngagementIntegrityStatus.FAILED,
            "reason_codes": reason_codes,
            "safe_ids": safe_ids,
            "redacted": True,
            "runtime_effect": False,
        },
        "incident_fingerprint",
    )


__all__ = [
    "build_blocked_incident",
    "build_evidence_bundle",
    "build_operator_review_item",
]
