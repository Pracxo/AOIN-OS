"""Deterministic taxonomy and computational expert profile registry."""

from __future__ import annotations

from collections.abc import Mapping

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    CaseRiskClass,
    DomainExpertProfile,
    DomainExpertProfileRegistry,
    DomainSpecialty,
    DomainTaxonomy,
    DomainTaxonomyNode,
    ExpertCapabilityScope,
    ExpertPerspectiveRole,
    domain_expert_profile_fingerprint,
    domain_expert_profile_registry_fingerprint,
    domain_specialty_fingerprint,
    domain_taxonomy_fingerprint,
    domain_taxonomy_node_fingerprint,
)

TOP_LEVEL_DOMAIN_IDS: tuple[str, ...] = (
    "business-and-management",
    "computing-and-information-systems",
    "cross-domain-methodology",
    "cybersecurity-and-digital-trust",
    "economics-and-finance",
    "education-and-learning",
    "engineering",
    "environment-and-earth-systems",
    "humanities",
    "law-and-regulation",
    "life-sciences",
    "mathematics-and-statistics",
    "medicine-and-health",
    "operations-and-supply-chain",
    "physical-sciences",
    "public-policy-and-government",
    "safety-risk-and-resilience",
    "social-sciences",
)

DOMAIN_LABELS: dict[str, str] = {
    "business-and-management": "Business and Management",
    "computing-and-information-systems": "Computing and Information Systems",
    "cross-domain-methodology": "Cross Domain Methodology",
    "cybersecurity-and-digital-trust": "Cybersecurity and Digital Trust",
    "economics-and-finance": "Economics and Finance",
    "education-and-learning": "Education and Learning",
    "engineering": "Engineering",
    "environment-and-earth-systems": "Environment and Earth Systems",
    "humanities": "Humanities",
    "law-and-regulation": "Law and Regulation",
    "life-sciences": "Life Sciences",
    "mathematics-and-statistics": "Mathematics and Statistics",
    "medicine-and-health": "Medicine and Health",
    "operations-and-supply-chain": "Operations and Supply Chain",
    "physical-sciences": "Physical Sciences",
    "public-policy-and-government": "Public Policy and Government",
    "safety-risk-and-resilience": "Safety Risk and Resilience",
    "social-sciences": "Social Sciences",
}

GENERAL_INPUT_KINDS: tuple[str, ...] = (
    "assessment-id",
    "claim-id",
    "domain-id",
    "risk-class",
    "scope-id",
    "specialty-id",
)
PROHIBITED_INPUT_KINDS: tuple[str, ...] = (
    "credential",
    "personal-data",
    "private-key",
    "raw-prompt",
    "source-body",
    "source-preview",
    "token",
)
ALL_RISKS: tuple[CaseRiskClass, ...] = (
    CaseRiskClass.CRITICAL,
    CaseRiskClass.HIGH,
    CaseRiskClass.LOW,
    CaseRiskClass.MODERATE,
)
HIGH_STAKES_RISKS: tuple[CaseRiskClass, ...] = (
    CaseRiskClass.CRITICAL,
    CaseRiskClass.HIGH,
)


def _with_fingerprint(
    payload: Mapping[str, object], field_name: str, fingerprint: str
) -> dict[str, object]:
    return {**payload, field_name: fingerprint}


def _specialty_for_domain(domain_id: str) -> DomainSpecialty:
    specialty_id = f"{domain_id}-general"
    payload = {
        "specialty_id": specialty_id,
        "domain_id": domain_id,
        "label": f"{DOMAIN_LABELS[domain_id]} General",
    }
    return DomainSpecialty.model_validate(
        _with_fingerprint(payload, "specialty_fingerprint", domain_specialty_fingerprint(payload))
    )


def build_default_domain_taxonomy() -> DomainTaxonomy:
    """Return the explicit AION-213 deterministic taxonomy."""

    specialties = tuple(_specialty_for_domain(domain_id) for domain_id in TOP_LEVEL_DOMAIN_IDS)
    nodes = tuple(
        DomainTaxonomyNode.model_validate(
            _with_fingerprint(
                {
                    "domain_id": domain_id,
                    "label": DOMAIN_LABELS[domain_id],
                    "specialty_ids": (f"{domain_id}-general",),
                },
                "node_fingerprint",
                domain_taxonomy_node_fingerprint(
                    {
                        "domain_id": domain_id,
                        "label": DOMAIN_LABELS[domain_id],
                        "specialty_ids": (f"{domain_id}-general",),
                    }
                ),
            )
        )
        for domain_id in TOP_LEVEL_DOMAIN_IDS
    )
    payload = {
        "nodes": nodes,
        "specialties": specialties,
        "top_level_domain_ids": TOP_LEVEL_DOMAIN_IDS,
    }
    return DomainTaxonomy.model_validate(
        _with_fingerprint(payload, "taxonomy_fingerprint", domain_taxonomy_fingerprint(payload))
    )


def _profile_payload(
    *,
    profile_id: str,
    domain_ids: tuple[str, ...],
    specialty_ids: tuple[str, ...],
    perspective_role: ExpertPerspectiveRole,
    independence_group_id: str,
    risk_classes: tuple[CaseRiskClass, ...] = ALL_RISKS,
    jurisdiction_ids: tuple[str, ...] = (),
    version_target_ids: tuple[str, ...] = (),
    temporal_scope_required: bool = False,
) -> dict[str, object]:
    capability_scope = ExpertCapabilityScope(
        domain_ids=domain_ids,
        specialty_ids=specialty_ids,
        jurisdiction_ids=jurisdiction_ids,
        version_target_ids=version_target_ids,
        supported_risk_classes=risk_classes,
        perspective_roles=(perspective_role,),
        temporal_scope_required=temporal_scope_required,
    )
    return {
        "profile_id": profile_id,
        "domain_ids": domain_ids,
        "specialty_ids": specialty_ids,
        "perspective_roles": (perspective_role,),
        "jurisdiction_ids": jurisdiction_ids,
        "version_target_ids": version_target_ids,
        "supported_risk_classes": risk_classes,
        "independence_group_id": independence_group_id,
        "required_input_kinds": GENERAL_INPUT_KINDS,
        "prohibited_input_kinds": PROHIBITED_INPUT_KINDS,
        "capability_scope": capability_scope,
    }


def _profile(
    *,
    profile_id: str,
    domain_ids: tuple[str, ...],
    specialty_ids: tuple[str, ...],
    perspective_role: ExpertPerspectiveRole,
    independence_group_id: str,
    risk_classes: tuple[CaseRiskClass, ...] = ALL_RISKS,
    jurisdiction_ids: tuple[str, ...] = (),
    version_target_ids: tuple[str, ...] = (),
    temporal_scope_required: bool = False,
) -> DomainExpertProfile:
    payload = _profile_payload(
        profile_id=profile_id,
        domain_ids=domain_ids,
        specialty_ids=specialty_ids,
        perspective_role=perspective_role,
        independence_group_id=independence_group_id,
        risk_classes=risk_classes,
        jurisdiction_ids=jurisdiction_ids,
        version_target_ids=version_target_ids,
        temporal_scope_required=temporal_scope_required,
    )
    return DomainExpertProfile.model_validate(
        _with_fingerprint(
            payload, "profile_fingerprint", domain_expert_profile_fingerprint(payload)
        )
    )


def build_default_profile_registry(
    taxonomy: DomainTaxonomy | None = None,
) -> DomainExpertProfileRegistry:
    """Return deterministic computational profiles with no human identity claims."""

    current_taxonomy = taxonomy or build_default_domain_taxonomy()
    domain_ids = current_taxonomy.top_level_domain_ids
    profiles: list[DomainExpertProfile] = []
    for domain_id in domain_ids:
        profiles.append(
            _profile(
                profile_id=f"computational-{domain_id}-domain-analyst",
                domain_ids=(domain_id,),
                specialty_ids=(f"{domain_id}-general",),
                perspective_role=ExpertPerspectiveRole.DOMAIN_ANALYST,
                independence_group_id=f"independence-{domain_id}-analyst",
            )
        )

    cross_domain_ids = tuple(domain_ids)
    cross_specialties = tuple(f"{domain_id}-general" for domain_id in domain_ids)
    profiles.extend(
        (
            _profile(
                profile_id="computational-cross-domain-evidence-auditor",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.EVIDENCE_AUDITOR,
                independence_group_id="independence-cross-domain-evidence",
            ),
            _profile(
                profile_id="computational-cross-domain-methodological-skeptic",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC,
                independence_group_id="independence-cross-domain-methodology",
            ),
            _profile(
                profile_id="computational-high-stakes-risk-reviewer",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.RISK_REVIEWER,
                independence_group_id="independence-high-stakes-risk",
                risk_classes=HIGH_STAKES_RISKS,
            ),
            _profile(
                profile_id="computational-temporal-scope-reviewer",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.TEMPORAL_SCOPE_REVIEWER,
                independence_group_id="independence-temporal-scope",
                temporal_scope_required=True,
            ),
            _profile(
                profile_id="computational-jurisdiction-scope-reviewer",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.JURISDICTION_REVIEWER,
                independence_group_id="independence-jurisdiction-scope",
                jurisdiction_ids=("eu", "global", "uk", "us"),
            ),
            _profile(
                profile_id="computational-version-scope-reviewer",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.VERSION_REVIEWER,
                independence_group_id="independence-version-scope",
                version_target_ids=("current", "v0.1", "v0.2"),
            ),
            _profile(
                profile_id="computational-synthesis-coordinator",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.SYNTHESIS_COORDINATOR,
                independence_group_id="independence-synthesis-coordination",
            ),
            _profile(
                profile_id="computational-cross-domain-reviewer",
                domain_ids=cross_domain_ids,
                specialty_ids=cross_specialties,
                perspective_role=ExpertPerspectiveRole.CROSS_DOMAIN_REVIEWER,
                independence_group_id="independence-cross-domain-review",
            ),
        )
    )
    ordered_profiles = tuple(sorted(profiles, key=lambda item: item.profile_id))
    payload = {"profiles": ordered_profiles}
    return DomainExpertProfileRegistry.model_validate(
        _with_fingerprint(
            payload,
            "registry_fingerprint",
            domain_expert_profile_registry_fingerprint(payload),
        )
    )


__all__ = [
    "ALL_RISKS",
    "DOMAIN_LABELS",
    "GENERAL_INPUT_KINDS",
    "HIGH_STAKES_RISKS",
    "PROHIBITED_INPUT_KINDS",
    "TOP_LEVEL_DOMAIN_IDS",
    "build_default_domain_taxonomy",
    "build_default_profile_registry",
]
