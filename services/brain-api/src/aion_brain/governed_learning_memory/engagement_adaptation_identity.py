"""Deterministic adaptation identity and conflict detection."""

from __future__ import annotations

from collections.abc import Iterable

from aion_brain.contracts.governed_engagement_learning import (
    EngagementAdaptationConflictFinding,
    EngagementAdaptationConflictReport,
    EngagementAdaptationIdentity,
    EngagementCandidateBinding,
    build_record,
    engagement_fingerprint,
)


def derive_engagement_adaptation_identity(
    *,
    binding: EngagementCandidateBinding,
    adaptation_scope_codes: tuple[str, ...] = ("candidate_enabled_for_shadow",),
) -> EngagementAdaptationIdentity:
    """Derive the stable adaptation identity without candidate version or approval."""

    subject_scope = engagement_fingerprint({"subjects": binding.subject_fingerprints})
    adaptation_scope = engagement_fingerprint({"scope": tuple(sorted(adaptation_scope_codes))})
    identity_id = (
        f"engagement-adaptation-{binding.candidate_kind.value}-"
        f"{subject_scope[:16]}-{adaptation_scope[:16]}"
    )
    payload = {
        "schema_version": "aion-glm-engagement-adaptation-identity/v1",
        "adaptation_identity_id": identity_id,
        "candidate_kind": binding.candidate_kind,
        "target_component_code": binding.target_component_code,
        "target_policy_code": binding.target_policy_code,
        "canonical_operation": binding.canonical_operation,
        "subject_scope_fingerprint": subject_scope,
        "adaptation_scope_fingerprint": adaptation_scope,
        "candidate_id": binding.learning_candidate_id,
        "candidate_fingerprint": binding.candidate_fingerprint,
        "runtime_effect": False,
    }
    return build_record(
        EngagementAdaptationIdentity,
        payload,
        "identity_fingerprint",
    )


def detect_engagement_duplicates_and_conflicts(
    *,
    identities: Iterable[EngagementAdaptationIdentity],
    overlay_fingerprints: dict[str, str],
    approval_bundle_fingerprints: dict[str, str],
) -> EngagementAdaptationConflictReport:
    """Preserve deterministic duplicates and material conflicts without precedence."""

    ordered = tuple(sorted(identities, key=lambda item: item.adaptation_identity_id))
    findings: list[EngagementAdaptationConflictFinding] = []
    seen: dict[tuple[str, str, str, str], str] = {}
    by_target: dict[tuple[str, str], str] = {}
    for identity in ordered:
        overlay_fp = overlay_fingerprints.get(identity.candidate_id, "")
        approval_fp = approval_bundle_fingerprints.get(identity.candidate_id, "")
        exact_key = (
            identity.adaptation_identity_id,
            identity.candidate_fingerprint,
            overlay_fp,
            approval_fp,
        )
        if exact_key in seen:
            findings.append(
                build_record(
                    EngagementAdaptationConflictFinding,
                    {
                        "finding_id": f"duplicate-{identity.candidate_id}",
                        "candidate_ids": tuple(sorted((seen[exact_key], identity.candidate_id))),
                        "adaptation_identity_id": identity.adaptation_identity_id,
                        "conflict_type": "duplicate",
                        "reason_codes": ("engagement_adaptation_duplicate",),
                        "redacted": True,
                        "runtime_effect": False,
                    },
                    "finding_fingerprint",
                )
            )
        else:
            seen[exact_key] = identity.candidate_id
        target_key = (identity.target_component_code, identity.target_policy_code)
        prior = by_target.get(target_key)
        if prior is not None and prior != identity.adaptation_identity_id:
            findings.append(
                build_record(
                    EngagementAdaptationConflictFinding,
                    {
                        "finding_id": f"target-conflict-{identity.candidate_id}",
                        "candidate_ids": tuple(
                            sorted(
                                item.candidate_id
                                for item in ordered
                                if (
                                    item.target_component_code,
                                    item.target_policy_code,
                                )
                                == target_key
                            )
                        ),
                        "adaptation_identity_id": identity.adaptation_identity_id,
                        "conflict_type": "target_conflict",
                        "reason_codes": ("engagement_target_conflict",),
                        "redacted": True,
                        "runtime_effect": False,
                    },
                    "finding_fingerprint",
                )
            )
        by_target.setdefault(target_key, identity.adaptation_identity_id)

    duplicate_count = sum(1 for item in findings if item.conflict_type == "duplicate")
    material_count = sum(1 for item in findings if item.conflict_type != "duplicate")
    reasons = ["engagement_adaptation_duplicate"] if duplicate_count else []
    if material_count:
        reasons.append("engagement_adaptation_conflict")
    if not reasons:
        reasons.append("engagement_safety_gate_passed")
    payload = {
        "schema_version": "aion-glm-engagement-adaptation-conflict/v1",
        "conflict_report_id": "engagement-conflict-report",
        "findings": tuple(sorted(findings, key=lambda item: item.finding_id)),
        "exact_duplicate_count": duplicate_count,
        "material_conflict_count": material_count,
        "unresolved_material_conflicts": material_count > 0,
        "reason_codes": tuple(reasons),
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(
        EngagementAdaptationConflictReport,
        payload,
        "report_fingerprint",
    )


__all__ = [
    "derive_engagement_adaptation_identity",
    "detect_engagement_duplicates_and_conflicts",
]
