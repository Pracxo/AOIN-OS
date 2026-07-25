"""Deterministic expert routing and independent panel selection."""

from __future__ import annotations

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    MAXIMUM_REQUIRED_ROLES_PER_PANEL,
    CaseRiskClass,
    DomainExpertCase,
    DomainExpertProfile,
    DomainExpertProfileRegistry,
    DomainTaxonomy,
    ExpertAssignment,
    ExpertPanelPlan,
    ExpertPerspectiveRole,
    domain_mesh_fingerprint,
    expert_assignment_fingerprint,
    expert_panel_plan_fingerprint,
)
from aion_brain.knowledge_intelligence.domain_expert_profiles import (
    build_default_domain_taxonomy,
    build_default_profile_registry,
)

ROUTING_POLICY_FINGERPRINT = domain_mesh_fingerprint(
    {
        "policy": "aion-domain-expert-routing-v1",
        "precedence": (
            "required perspective role match",
            "exact specialty match",
            "exact domain match",
            "exact jurisdiction match",
            "exact version-target match",
            "explicit temporal-scope compatibility",
            "risk-class support",
            "distinct independence group",
            "lexicographically smallest profile ID",
        ),
    },
    "routing_policy_fingerprint",
)


def required_panel_roles(case: DomainExpertCase) -> tuple[ExpertPerspectiveRole, ...]:
    """Return deterministic required roles for an explicit case."""

    roles: list[ExpertPerspectiveRole] = [
        ExpertPerspectiveRole.DOMAIN_ANALYST,
        ExpertPerspectiveRole.EVIDENCE_AUDITOR,
        ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC,
    ]
    if case.risk_class in {CaseRiskClass.HIGH, CaseRiskClass.CRITICAL}:
        roles.append(ExpertPerspectiveRole.RISK_REVIEWER)
    if case.target_valid_time is not None:
        roles.append(ExpertPerspectiveRole.TEMPORAL_SCOPE_REVIEWER)
    if case.target_jurisdiction_ids:
        roles.append(ExpertPerspectiveRole.JURISDICTION_REVIEWER)
    if case.target_version_ids:
        roles.append(ExpertPerspectiveRole.VERSION_REVIEWER)
    if len(case.domain_ids) > 1:
        roles.append(ExpertPerspectiveRole.CROSS_DOMAIN_REVIEWER)
    roles.append(ExpertPerspectiveRole.SYNTHESIS_COORDINATOR)
    if len(roles) <= MAXIMUM_REQUIRED_ROLES_PER_PANEL:
        return tuple(roles)

    # Preserve hard required roles and bounded policy. The omitted applicable role
    # is reported as missing through panel abstention instead of expanding budget.
    bounded = roles[: MAXIMUM_REQUIRED_ROLES_PER_PANEL - 1]
    if ExpertPerspectiveRole.SYNTHESIS_COORDINATOR not in bounded:
        bounded.append(ExpertPerspectiveRole.SYNTHESIS_COORDINATOR)
    return tuple(bounded[:MAXIMUM_REQUIRED_ROLES_PER_PANEL])


def find_eligible_profiles(
    case: DomainExpertCase,
    registry: DomainExpertProfileRegistry | None = None,
    *,
    role: ExpertPerspectiveRole | None = None,
    taxonomy: DomainTaxonomy | None = None,
) -> tuple[DomainExpertProfile, ...]:
    """Find profiles that exactly match explicit case metadata."""

    current_taxonomy = taxonomy or build_default_domain_taxonomy()
    current_registry = registry or build_default_profile_registry(current_taxonomy)
    known_domains = {node.domain_id for node in current_taxonomy.nodes}
    known_specialties = {specialty.specialty_id for specialty in current_taxonomy.specialties}
    if set(case.domain_ids) - known_domains:
        return ()
    if set(case.specialty_ids) - known_specialties:
        return ()

    eligible: list[DomainExpertProfile] = []
    for profile in current_registry.profiles:
        if role is not None and role not in profile.perspective_roles:
            continue
        if case.risk_class not in profile.supported_risk_classes:
            continue
        if not set(case.domain_ids).intersection(profile.domain_ids):
            continue
        if case.specialty_ids and not set(case.specialty_ids).intersection(profile.specialty_ids):
            continue
        if role == ExpertPerspectiveRole.JURISDICTION_REVIEWER and case.target_jurisdiction_ids:
            if not set(case.target_jurisdiction_ids).intersection(profile.jurisdiction_ids):
                continue
        if role == ExpertPerspectiveRole.VERSION_REVIEWER and case.target_version_ids:
            if not set(case.target_version_ids).intersection(profile.version_target_ids):
                continue
        eligible.append(profile)
    return tuple(sorted(eligible, key=lambda item: item.profile_id))


def rank_eligible_profiles(
    case: DomainExpertCase,
    profiles: tuple[DomainExpertProfile, ...],
    *,
    role: ExpertPerspectiveRole,
    used_independence_groups: frozenset[str] = frozenset(),
) -> tuple[DomainExpertProfile, ...]:
    """Rank eligible profiles by explicit deterministic precedence."""

    case_specialties = set(case.specialty_ids)
    case_domains = set(case.domain_ids)
    case_jurisdictions = set(case.target_jurisdiction_ids)
    case_versions = set(case.target_version_ids)

    def precedence(
        profile: DomainExpertProfile,
    ) -> tuple[int, int, int, int, int, int, int, int, str]:
        return (
            0 if role in profile.perspective_roles else 1,
            -len(case_specialties.intersection(profile.specialty_ids)),
            -len(case_domains.intersection(profile.domain_ids)),
            -len(case_jurisdictions.intersection(profile.jurisdiction_ids)),
            -len(case_versions.intersection(profile.version_target_ids)),
            0
            if (
                case.target_valid_time is None
                or role != ExpertPerspectiveRole.TEMPORAL_SCOPE_REVIEWER
                or profile.capability_scope.temporal_scope_required
            )
            else 1,
            0 if case.risk_class in profile.supported_risk_classes else 1,
            1 if profile.independence_group_id in used_independence_groups else 0,
            profile.profile_id,
        )

    return tuple(sorted(profiles, key=precedence))


def select_expert_panel(
    case: DomainExpertCase,
    registry: DomainExpertProfileRegistry | None = None,
    *,
    taxonomy: DomainTaxonomy | None = None,
) -> ExpertPanelPlan:
    """Select an independent deterministic panel or require abstention."""

    current_taxonomy = taxonomy or build_default_domain_taxonomy()
    current_registry = registry or build_default_profile_registry(current_taxonomy)
    required_roles = required_panel_roles(case)
    assignments: list[ExpertAssignment] = []
    missing: list[ExpertPerspectiveRole] = []
    used_profiles: set[str] = set()
    used_groups: set[str] = set()
    reason_codes: list[str] = []

    for role in required_roles:
        ranked = rank_eligible_profiles(
            case,
            find_eligible_profiles(case, current_registry, role=role, taxonomy=current_taxonomy),
            role=role,
            used_independence_groups=frozenset(used_groups),
        )
        selected = next(
            (
                profile
                for profile in ranked
                if profile.profile_id not in used_profiles
                and profile.independence_group_id not in used_groups
            ),
            None,
        )
        if selected is None:
            missing.append(role)
            reason_codes.append("domain_mesh_required_role_missing")
            continue
        used_profiles.add(selected.profile_id)
        used_groups.add(selected.independence_group_id)
        domain_matches = tuple(sorted(set(case.domain_ids).intersection(selected.domain_ids)))
        specialty_matches = tuple(
            sorted(set(case.specialty_ids).intersection(selected.specialty_ids))
        )
        jurisdiction_matches = tuple(
            sorted(set(case.target_jurisdiction_ids).intersection(selected.jurisdiction_ids))
        )
        version_matches = tuple(
            sorted(set(case.target_version_ids).intersection(selected.version_target_ids))
        )
        payload = {
            "assignment_id": f"assignment-{case.case_id}-{role.value}",
            "profile_id": selected.profile_id,
            "perspective_role": role,
            "independence_group_id": selected.independence_group_id,
            "domain_match_ids": domain_matches,
            "specialty_match_ids": specialty_matches,
            "jurisdiction_match_ids": jurisdiction_matches,
            "version_match_ids": version_matches,
            "temporal_scope_match": case.target_valid_time is not None
            and role == ExpertPerspectiveRole.TEMPORAL_SCOPE_REVIEWER,
            "risk_class_match": case.risk_class in selected.supported_risk_classes,
            "required_role": True,
        }
        assignments.append(
            ExpertAssignment.model_validate(
                {**payload, "assignment_fingerprint": expert_assignment_fingerprint(payload)}
            )
        )
        reason_codes.extend(
            [
                "domain_mesh_required_role_assigned",
                "domain_mesh_domain_match",
                "domain_mesh_risk_match",
            ]
        )
        if specialty_matches:
            reason_codes.append("domain_mesh_specialty_match")
        if jurisdiction_matches:
            reason_codes.append("domain_mesh_jurisdiction_match")
        if version_matches:
            reason_codes.append("domain_mesh_version_match")
        if case.target_valid_time is not None:
            reason_codes.append("domain_mesh_temporal_scope_match")

    if missing:
        reason_codes.append("domain_mesh_panel_incomplete")
    else:
        reason_codes.append("domain_mesh_panel_selected")
    if len(assignments) != len({item.independence_group_id for item in assignments}):
        reason_codes.append("domain_mesh_independence_group_duplicate")

    unique_reason_codes = tuple(dict.fromkeys(reason_codes))
    explicit_abstention_required = bool(missing) or case.risk_class in {
        CaseRiskClass.HIGH,
        CaseRiskClass.CRITICAL,
    }
    payload = {
        "panel_id": f"panel-{case.case_id}",
        "case_id": case.case_id,
        "assignments": tuple(sorted(assignments, key=lambda item: item.assignment_id)),
        "required_roles": required_roles,
        "optional_roles": (),
        "missing_required_roles": tuple(missing),
        "panel_size": len(assignments),
        "independence_group_count": len({item.independence_group_id for item in assignments}),
        "routing_reason_codes": unique_reason_codes,
        "routing_policy_fingerprint": ROUTING_POLICY_FINGERPRINT,
        "operator_review_required": explicit_abstention_required,
        "explicit_abstention_required": explicit_abstention_required,
    }
    return ExpertPanelPlan.model_validate(
        {**payload, "panel_fingerprint": expert_panel_plan_fingerprint(payload)}
    )


__all__ = [
    "ROUTING_POLICY_FINGERPRINT",
    "find_eligible_profiles",
    "rank_eligible_profiles",
    "required_panel_roles",
    "select_expert_panel",
]
