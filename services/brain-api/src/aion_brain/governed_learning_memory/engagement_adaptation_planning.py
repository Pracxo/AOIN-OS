"""Append-only in-memory adaptation version and target policy planning."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.governed_engagement_learning import (
    EngagementAdaptationIdentity,
    EngagementAdaptationVersionDisposition,
    EngagementAdaptationVersionPlan,
    EngagementApplicationApprovalBundle,
    EngagementTargetPolicy,
    build_record,
    engagement_fingerprint,
    target_spec_for_candidate_kind,
    utc_now,
)


def plan_engagement_adaptation_version(
    *,
    version_plan_id: str,
    identity: EngagementAdaptationIdentity,
    approval_bundle: EngagementApplicationApprovalBundle,
    candidate_version: int,
    effective_from: datetime | None = None,
    expires_at: datetime,
    previous_versions: tuple[EngagementAdaptationVersionPlan, ...] = (),
    supersedes_version_id: str | None = None,
    retracts_version_id: str | None = None,
) -> EngagementAdaptationVersionPlan:
    """Plan a deterministic append-only adaptation version in memory."""

    ordered = tuple(sorted(previous_versions, key=lambda item: item.planned_version_number))
    if ordered:
        expected_numbers = tuple(range(1, len(ordered) + 1))
        actual_numbers = tuple(item.planned_version_number for item in ordered)
        if actual_numbers != expected_numbers:
            raise ValueError("previous versions must be contiguous")
    planned = len(ordered) + 1
    previous_id = ordered[-1].version_plan_id if ordered else None
    if retracts_version_id is not None:
        disposition = EngagementAdaptationVersionDisposition.RETRACTION_PLANNED
        reason = "engagement_version_retraction_planned"
    elif supersedes_version_id is not None:
        disposition = EngagementAdaptationVersionDisposition.SUPERSESSION_PLANNED
        reason = "engagement_version_supersession_planned"
    elif planned == 1:
        disposition = EngagementAdaptationVersionDisposition.INITIAL_VERSION_PLANNED
        reason = "engagement_version_initial_planned"
    else:
        disposition = EngagementAdaptationVersionDisposition.NEW_VERSION_PLANNED
        reason = "engagement_version_new_planned"
    payload = {
        "schema_version": "aion-glm-engagement-adaptation-version/v1",
        "version_plan_id": version_plan_id,
        "adaptation_identity_id": identity.adaptation_identity_id,
        "disposition": disposition,
        "planned_version_number": planned,
        "previous_version_id": previous_id,
        "candidate_id": identity.candidate_id,
        "candidate_fingerprint": identity.candidate_fingerprint,
        "candidate_version": candidate_version,
        "target_component_code": identity.target_component_code,
        "target_policy_code": identity.target_policy_code,
        "canonical_operation": identity.canonical_operation,
        "approval_bundle_fingerprint": approval_bundle.bundle_fingerprint,
        "effective_from": effective_from or utc_now(),
        "expires_at": expires_at,
        "supersedes_version_id": supersedes_version_id,
        "retracts_version_id": retracts_version_id,
        "append_only": True,
        "historical_versions_preserved": True,
        "persistent_version_created": False,
        "reason_codes": (reason, "engagement_expiry_valid"),
        "runtime_effect": False,
    }
    return build_record(
        EngagementAdaptationVersionPlan,
        payload,
        "version_plan_fingerprint",
    )


def build_engagement_target_policy(
    *,
    target_policy_id: str,
    identity: EngagementAdaptationIdentity,
    bounded_parameter_codes: tuple[str, ...] = (
        "review_required",
        "candidate_enabled_for_shadow",
        "baseline_fallback_required",
    ),
) -> EngagementTargetPolicy:
    """Build a closed-registry target policy for deterministic shadow simulation."""

    spec = target_spec_for_candidate_kind(identity.candidate_kind)
    payload = {
        "schema_version": "aion-glm-engagement-target-policy/v1",
        "target_policy_id": target_policy_id,
        "candidate_kind": identity.candidate_kind,
        "target_component_code": spec.target_component_code,
        "target_policy_code": spec.target_policy_code,
        "canonical_operation": spec.canonical_operation,
        "bounded_parameter_codes": tuple(sorted(bounded_parameter_codes)),
        "target_scope_fingerprint": engagement_fingerprint(
            {
                "component": spec.target_component_code,
                "policy": spec.target_policy_code,
                "operation": spec.canonical_operation.value,
                "subject": identity.subject_scope_fingerprint,
            }
        ),
        "production_component_reference_present": False,
        "production_policy_mutation_authorized": False,
        "persistent_write_authorized": False,
        "runtime_effect": False,
    }
    return build_record(EngagementTargetPolicy, payload, "policy_fingerprint")


__all__ = [
    "build_engagement_target_policy",
    "plan_engagement_adaptation_version",
]
