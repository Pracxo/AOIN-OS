"""Evidence contribution and source-independence scoring."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from aion_brain.contracts.knowledge_claim_graph import ClaimEvidenceBinding, EvidenceRole
from aion_brain.contracts.knowledge_epistemic_assessment import (
    SOURCE_QUALITY_METADATA_FACTORS,
    EpistemicFreshnessPolicy,
    EvidenceContribution,
    EvidenceGroupDisposition,
    FreshnessStatus,
    RoleEvidenceScore,
    ScopeApplicability,
    evidence_contribution_fingerprint,
    quantize_score,
    role_evidence_score_fingerprint,
)
from aion_brain.contracts.knowledge_research import ResearchSourceClass
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredDeduplicationDecision,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryPayload,
    SourceRegistryRecordEnvelope,
)
from aion_brain.knowledge_intelligence.epistemic_freshness import evaluate_payload_freshness


@dataclass(frozen=True)
class ContributionIndexes:
    """Source-registry lookup indexes for contribution resolution."""

    by_record_id: Mapping[str, SourceRegistryRecordEnvelope]
    duplicate_snapshot_ids: frozenset[str]
    mirror_snapshot_ids: frozenset[str]


def build_contribution_indexes(
    records: Iterable[SourceRegistryRecordEnvelope],
) -> ContributionIndexes:
    """Build immutable lookup indexes over registry records."""

    by_record_id = {record.record_id: record for record in records}
    duplicate_snapshot_ids: set[str] = set()
    mirror_snapshot_ids: set[str] = set()
    for record in by_record_id.values():
        payload = record.payload
        if isinstance(payload, RegisteredDeduplicationDecision):
            if (
                payload.exact_url_duplicate
                or payload.canonical_url_duplicate
                or payload.exact_content_duplicate
            ):
                duplicate_snapshot_ids.add(payload.snapshot_id)
            if payload.redirect_alias or payload.suspected_mirror:
                mirror_snapshot_ids.add(payload.snapshot_id)
    return ContributionIndexes(
        by_record_id=by_record_id,
        duplicate_snapshot_ids=frozenset(duplicate_snapshot_ids),
        mirror_snapshot_ids=frozenset(mirror_snapshot_ids),
    )


def source_quality_factor(source_class: ResearchSourceClass) -> Decimal:
    """Return the versioned source-quality metadata factor."""

    return SOURCE_QUALITY_METADATA_FACTORS[source_class].quantize(Decimal("0.000001"))


def resolve_evidence_contributions(
    bindings: Iterable[ClaimEvidenceBinding],
    *,
    indexes: ContributionIndexes,
    claim_scope_factors: tuple[
        ScopeApplicability, Decimal, ScopeApplicability, Decimal, ScopeApplicability, Decimal
    ],
    freshness_policy: EpistemicFreshnessPolicy,
    assessment_time: datetime,
) -> tuple[EvidenceContribution, ...]:
    """Resolve graph evidence bindings into redacted contribution records."""

    binding_values = tuple(sorted(bindings, key=lambda item: item.binding_id))
    group_roles: defaultdict[str, set[EvidenceRole]] = defaultdict(set)
    for binding in binding_values:
        group_id = _binding_independence_group(binding)
        if binding.evidence_role in {EvidenceRole.SUPPORTS, EvidenceRole.OPPOSES}:
            group_roles[group_id].add(binding.evidence_role)
    ambiguous_groups = {
        group_id
        for group_id, roles in group_roles.items()
        if EvidenceRole.SUPPORTS in roles and EvidenceRole.OPPOSES in roles
    }

    seen_role_groups: set[tuple[EvidenceRole, str]] = set()
    contributions: list[EvidenceContribution] = []
    for binding in binding_values:
        group_id = _binding_independence_group(binding)
        role_group = (binding.evidence_role, group_id)
        duplicate = (
            role_group in seen_role_groups or binding.evidence_role == EvidenceRole.DUPLICATE
        )
        seen_role_groups.add(role_group)
        mirror = _binding_has_mirror_snapshot(binding, indexes)
        ambiguous = group_id in ambiguous_groups
        disposition = _disposition(binding.evidence_role, duplicate, mirror, ambiguous)
        contribution = _contribution_for_binding(
            binding,
            indexes=indexes,
            group_id=group_id,
            disposition=disposition,
            duplicate=duplicate,
            mirror=mirror,
            ambiguous=ambiguous,
            claim_scope_factors=claim_scope_factors,
            freshness_policy=freshness_policy,
            assessment_time=assessment_time,
        )
        contributions.append(contribution)
    return tuple(contributions)


def score_role(
    *,
    claim_id: str,
    role: str,
    contributions: Iterable[EvidenceContribution],
) -> RoleEvidenceScore:
    """Score counted evidence for one evidence role."""

    role_contributions = tuple(
        item
        for item in contributions
        if _role_matches(item.evidence_role, role)
        and item.disposition
        in {EvidenceGroupDisposition.COUNTED_SUPPORT, EvidenceGroupDisposition.COUNTED_OPPOSITION}
    )
    declared = tuple(item for item in contributions if _role_matches(item.evidence_role, role))
    independent_groups = {item.independence_group_id for item in role_contributions}
    if not role_contributions:
        payload = _role_score_payload(
            claim_id=claim_id,
            role=role,
            independent_group_count=0,
            declared_group_count=len({item.independence_group_id for item in declared}),
            representative_binding_ids=(),
            reason_codes=(),
        )
        return RoleEvidenceScore.model_validate(
            {**payload, "score_fingerprint": role_evidence_score_fingerprint(payload)}
        )

    reference_resolution = _average(item.reference_resolution_score for item in role_contributions)
    evidence_coverage = _average(item.evidence_coverage_score for item in role_contributions)
    citation_coverage = _average(item.citation_coverage_score for item in role_contributions)
    provenance = _average(item.provenance_completeness_score for item in role_contributions)
    source_quality = _average(item.source_quality_metadata_factor for item in role_contributions)
    valid_time = _average(item.valid_time_factor for item in role_contributions)
    jurisdiction = _average(item.jurisdiction_factor for item in role_contributions)
    version = _average(item.version_factor for item in role_contributions)
    freshness = _average(item.freshness_factor for item in role_contributions)
    source_independence = quantize_score(min(len(independent_groups), 2) / Decimal("2"))
    reason = (
        "epistemic_independent_support_counted"
        if role == "support"
        else "epistemic_independent_opposition_counted"
    )
    payload = _role_score_payload(
        claim_id=claim_id,
        role=role,
        independent_group_count=len(independent_groups),
        declared_group_count=len({item.independence_group_id for item in declared}),
        representative_binding_ids=tuple(item.binding_id for item in role_contributions),
        reason_codes=(reason,),
        reference_resolution=reference_resolution,
        evidence_coverage=evidence_coverage,
        citation_coverage=citation_coverage,
        provenance_completeness=provenance,
        source_independence=source_independence,
        source_quality_metadata=source_quality,
        valid_time_applicability=valid_time,
        jurisdiction_applicability=jurisdiction,
        version_applicability=version,
        freshness=freshness,
    )
    return RoleEvidenceScore.model_validate(
        {**payload, "score_fingerprint": role_evidence_score_fingerprint(payload)}
    )


def counted_contributions(
    contributions: Iterable[EvidenceContribution],
) -> tuple[EvidenceContribution, ...]:
    """Return only contributions counted in support or opposition scores."""

    counted = {
        EvidenceGroupDisposition.COUNTED_SUPPORT,
        EvidenceGroupDisposition.COUNTED_OPPOSITION,
    }
    return tuple(item for item in contributions if item.disposition in counted)


def _contribution_for_binding(
    binding: ClaimEvidenceBinding,
    *,
    indexes: ContributionIndexes,
    group_id: str,
    disposition: EvidenceGroupDisposition,
    duplicate: bool,
    mirror: bool,
    ambiguous: bool,
    claim_scope_factors: tuple[
        ScopeApplicability, Decimal, ScopeApplicability, Decimal, ScopeApplicability, Decimal
    ],
    freshness_policy: EpistemicFreshnessPolicy,
    assessment_time: datetime,
) -> EvidenceContribution:
    valid_time_applicability, valid_time_factor = claim_scope_factors[0], claim_scope_factors[1]
    jurisdiction_applicability = claim_scope_factors[2]
    jurisdiction_factor = claim_scope_factors[3]
    version_applicability = claim_scope_factors[4]
    version_factor = claim_scope_factors[5]
    source_payload = _first_payload(binding.source_snapshot_record_ids, indexes)
    source_class = _source_class(source_payload)
    reference_resolution = (
        Decimal("1.000000") if _all_references_resolved(binding, indexes) else Decimal("0")
    )
    evidence_coverage = Decimal("1.000000") if binding.source_registry_record_ids else Decimal("0")
    citation_coverage = Decimal("1.000000") if binding.citation_record_ids else Decimal("0")
    provenance = Decimal("1.000000") if binding.source_provenance_record_ids else Decimal("0")
    if source_payload is None:
        freshness = (FreshnessStatus.UNKNOWN, Decimal("0.000000"))
    else:
        evaluation = evaluate_payload_freshness(
            source_payload,
            policy=freshness_policy,
            assessment_time=assessment_time,
        )
        freshness = (evaluation.status, evaluation.factor)
    payload = {
        "schema_version": "aion-knowledge-evidence-contribution/v1",
        "claim_id": binding.claim_id,
        "binding_id": binding.binding_id,
        "evidence_role": binding.evidence_role,
        "independence_group_id": group_id,
        "source_registry_record_ids": binding.source_registry_record_ids,
        "citation_record_ids": binding.citation_record_ids,
        "provenance_record_ids": binding.source_provenance_record_ids,
        "source_class": source_class,
        "source_quality_metadata_factor": source_quality_factor(source_class),
        "reference_resolution_score": reference_resolution,
        "evidence_coverage_score": evidence_coverage,
        "citation_coverage_score": citation_coverage,
        "provenance_completeness_score": provenance,
        "freshness_status": freshness[0],
        "freshness_factor": freshness[1],
        "valid_time_applicability": valid_time_applicability,
        "valid_time_factor": valid_time_factor,
        "jurisdiction_applicability": jurisdiction_applicability,
        "jurisdiction_factor": jurisdiction_factor,
        "version_applicability": version_applicability,
        "version_factor": version_factor,
        "disposition": disposition,
        "duplicate_suppressed": duplicate,
        "mirror_suppressed": mirror,
        "role_ambiguous": ambiguous,
        "claim_verified": False,
        "truth_effect": False,
        "confidence_effect_only": True,
        "knowledge_effect": False,
        "belief_effect": False,
        "runtime_effect": False,
    }
    return EvidenceContribution.model_validate(
        {
            **payload,
            "contribution_fingerprint": evidence_contribution_fingerprint(payload),
        }
    )


def _role_score_payload(
    *,
    claim_id: str,
    role: str,
    independent_group_count: int,
    declared_group_count: int,
    representative_binding_ids: tuple[str, ...],
    reason_codes: tuple[str, ...],
    reference_resolution: Decimal = Decimal("0.000000"),
    evidence_coverage: Decimal = Decimal("0.000000"),
    citation_coverage: Decimal = Decimal("0.000000"),
    provenance_completeness: Decimal = Decimal("0.000000"),
    source_independence: Decimal = Decimal("0.000000"),
    source_quality_metadata: Decimal = Decimal("0.000000"),
    valid_time_applicability: Decimal = Decimal("0.000000"),
    jurisdiction_applicability: Decimal = Decimal("0.000000"),
    version_applicability: Decimal = Decimal("0.000000"),
    freshness: Decimal = Decimal("0.000000"),
) -> dict[str, object]:
    raw = (
        reference_resolution * Decimal("0.10")
        + evidence_coverage * Decimal("0.10")
        + citation_coverage * Decimal("0.10")
        + provenance_completeness * Decimal("0.10")
        + source_independence * Decimal("0.25")
        + source_quality_metadata * Decimal("0.10")
        + valid_time_applicability * Decimal("0.08")
        + jurisdiction_applicability * Decimal("0.06")
        + version_applicability * Decimal("0.06")
        + freshness * Decimal("0.05")
    )
    return {
        "schema_version": "aion-knowledge-role-evidence-score/v1",
        "claim_id": claim_id,
        "role": role,
        "reference_resolution": reference_resolution,
        "evidence_coverage": evidence_coverage,
        "citation_coverage": citation_coverage,
        "provenance_completeness": provenance_completeness,
        "source_independence": source_independence,
        "source_quality_metadata": source_quality_metadata,
        "valid_time_applicability": valid_time_applicability,
        "jurisdiction_applicability": jurisdiction_applicability,
        "version_applicability": version_applicability,
        "freshness": freshness,
        "independent_group_count": independent_group_count,
        "declared_group_count": declared_group_count,
        "representative_binding_ids": representative_binding_ids,
        "raw_role_score": quantize_score(raw),
        "reason_codes": reason_codes,
        "runtime_effect": False,
    }


def _binding_independence_group(binding: ClaimEvidenceBinding) -> str:
    if binding.lineage_group_ids:
        return sorted(binding.lineage_group_ids)[0]
    return f"binding-group-{binding.binding_id}"


def _binding_has_mirror_snapshot(
    binding: ClaimEvidenceBinding,
    indexes: ContributionIndexes,
) -> bool:
    for record_id in binding.source_snapshot_record_ids:
        record = indexes.by_record_id.get(record_id)
        if record is not None and isinstance(record.payload, RegisteredSourceSnapshotDigest):
            if record.payload.snapshot_id in indexes.mirror_snapshot_ids:
                return True
            if record.payload.snapshot_id in indexes.duplicate_snapshot_ids:
                return True
    return False


def _disposition(
    role: EvidenceRole,
    duplicate: bool,
    mirror: bool,
    ambiguous: bool,
) -> EvidenceGroupDisposition:
    if role == EvidenceRole.CONTEXT:
        return EvidenceGroupDisposition.CONTEXT_ONLY
    if ambiguous:
        return EvidenceGroupDisposition.ROLE_AMBIGUOUS
    if mirror:
        return EvidenceGroupDisposition.MIRROR_SUPPRESSED
    if duplicate:
        return EvidenceGroupDisposition.DUPLICATE_SUPPRESSED
    if role == EvidenceRole.SUPPORTS:
        return EvidenceGroupDisposition.COUNTED_SUPPORT
    if role == EvidenceRole.OPPOSES:
        return EvidenceGroupDisposition.COUNTED_OPPOSITION
    return EvidenceGroupDisposition.DUPLICATE_SUPPRESSED


def _first_payload(
    record_ids: tuple[str, ...],
    indexes: ContributionIndexes,
) -> SourceRegistryPayload | None:
    for record_id in record_ids:
        record = indexes.by_record_id.get(record_id)
        if record is not None:
            return record.payload
    return None


def _source_class(payload: SourceRegistryPayload | None) -> ResearchSourceClass:
    if isinstance(payload, (RegisteredSourceSnapshotDigest, RegisteredSourceProvenance)):
        return payload.source_class
    return "unknown"


def _all_references_resolved(
    binding: ClaimEvidenceBinding,
    indexes: ContributionIndexes,
) -> bool:
    all_ids = (
        *binding.source_registry_record_ids,
        *binding.source_snapshot_record_ids,
        *binding.source_provenance_record_ids,
        *binding.citation_record_ids,
        *binding.lineage_record_ids,
    )
    return bool(all_ids) and all(record_id in indexes.by_record_id for record_id in all_ids)


def _average(values: Iterable[Decimal]) -> Decimal:
    collected = tuple(values)
    if not collected:
        return quantize_score("0")
    return quantize_score(sum(collected, Decimal("0")) / Decimal(len(collected)))


def _role_matches(role: EvidenceRole, expected: str) -> bool:
    if expected == "support":
        return role == EvidenceRole.SUPPORTS
    return role == EvidenceRole.OPPOSES


__all__ = [
    "ContributionIndexes",
    "build_contribution_indexes",
    "counted_contributions",
    "resolve_evidence_contributions",
    "score_role",
    "source_quality_factor",
]
