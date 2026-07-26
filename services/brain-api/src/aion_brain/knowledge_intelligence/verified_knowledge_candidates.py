"""Verified-knowledge candidate eligibility and construction."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import (
    ConfidenceBand,
    ContradictionStatus,
    EpistemicAssessmentStatus,
    FreshnessStatus,
    ScopeApplicability,
)
from aion_brain.contracts.knowledge_verified_memory import (
    VERIFIED_KNOWLEDGE_CANDIDATE_SCHEMA_VERSION,
    VERIFIED_KNOWLEDGE_ELIGIBILITY_SCHEMA_VERSION,
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateEligibilityInput,
    VerifiedKnowledgeCandidateKind,
    VerifiedKnowledgeEligibilityDecision,
    VerifiedKnowledgeEligibilityStatus,
    VerifiedKnowledgeLifecycleStatus,
    candidate_identity_id,
    quantize_confidence,
    utc_now,
    verified_knowledge_fingerprint,
)


def _confidence_cap(source: VerifiedKnowledgeCandidateEligibilityInput) -> Decimal:
    values: list[Decimal] = [
        source.assessment_confidence,
        source.assessment_hard_cap,
        source.synthesis_confidence_cap,
        *source.required_report_confidence_caps,
        *source.tool_evidence_confidence_caps,
    ]
    return min(values) if values else Decimal("0.000000")


def _band(value: Decimal) -> ConfidenceBand:
    if value >= Decimal("0.950000"):
        return ConfidenceBand.VERY_HIGH
    if value >= Decimal("0.850000"):
        return ConfidenceBand.HIGH
    if value >= Decimal("0.600000"):
        return ConfidenceBand.MEDIUM
    if value >= Decimal("0.300000"):
        return ConfidenceBand.LOW
    return ConfidenceBand.VERY_LOW


def _support_evidence_count(source: VerifiedKnowledgeCandidateEligibilityInput) -> int:
    return (
        source.independent_support_count
        if source.candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
        else source.independent_opposition_count
    )


def _expected_assessment_status(
    candidate_kind: VerifiedKnowledgeCandidateKind,
) -> EpistemicAssessmentStatus:
    if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE:
        return EpistemicAssessmentStatus.SUPPORTED
    return EpistemicAssessmentStatus.CONTRADICTED


def evaluate_verified_knowledge_candidate_eligibility(
    source: VerifiedKnowledgeCandidateEligibilityInput,
) -> VerifiedKnowledgeEligibilityDecision:
    """Evaluate support/refutation eligibility without confidence amplification."""

    cap = _confidence_cap(source)
    reason_codes: list[str] = [
        "verified_candidate_confidence_inherited",
        "verified_candidate_confidence_non_amplification_enforced",
        "verified_candidate_tool_output_not_fact",
        "verified_candidate_engagement_not_fact",
        "verified_candidate_operator_review_required",
        "verified_candidate_automatic_promotion_blocked",
        "verified_candidate_cognitive_memory_write_blocked",
        "verified_candidate_belief_mutation_blocked",
        "verified_candidate_persistent_write_disabled",
        "verified_candidate_runtime_disabled",
    ]
    integrity_checks = (
        source.source_registry_integrity_passed,
        source.claim_graph_integrity_passed,
        source.epistemic_assessment_integrity_passed,
        source.domain_mesh_integrity_passed,
        source.tool_verification_integrity_passed,
        source.tool_attestation_chains_valid,
        not source.actual_tool_executed,
        not source.tool_output_used_as_fact,
        not source.engagement_used_as_fact,
        not source.engagement_confidence_effect,
    )
    if not all(integrity_checks):
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INTEGRITY_FAILURE
        reason_codes.append("verified_candidate_integrity_failed")
    elif source.retraction_applicable:
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_RETRACTED
        reason_codes.append("verified_candidate_retracted")
    elif source.supersession_applicable and not source.current_evidence_after_supersession:
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_SUPERSEDED
        reason_codes.append("verified_candidate_superseded")
    elif source.freshness_status is not FreshnessStatus.CURRENT:
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_STALE
        reason_codes.append("verified_candidate_stale")
    elif source.scope_applicability_status is not ScopeApplicability.APPLICABLE:
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_SCOPE_MISMATCH
        reason_codes.append("verified_candidate_scope_mismatch")
    elif source.contradiction_status not in {
        ContradictionStatus.NONE_DETECTED,
        ContradictionStatus.SCOPE_SEPARATED,
    }:
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_UNRESOLVED_CONTRADICTION
        reason_codes.append("verified_candidate_unresolved_contradiction")
    elif (
        source.unresolved_material_dissent
        or not source.required_mesh_roles_complete
        or source.unresolved_material_support_conflict
        or source.unresolved_material_opposition_conflict
    ):
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_MATERIAL_DISSENT
        reason_codes.append("verified_candidate_material_dissent")
    elif source.provenance_completeness != Decimal("1.000000"):
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INCOMPLETE_PROVENANCE
        reason_codes.append("verified_candidate_incomplete_provenance")
    elif source.citation_coverage != Decimal("1.000000"):
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INCOMPLETE_CITATIONS
        reason_codes.append("verified_candidate_incomplete_citations")
    elif (
        source.evidence_coverage != Decimal("1.000000")
        or _support_evidence_count(source) < 3
        or source.assessment_status != _expected_assessment_status(source.candidate_kind)
    ):
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_INSUFFICIENT_EVIDENCE
        reason_codes.append("verified_candidate_insufficient_evidence")
    elif cap < Decimal("0.850000"):
        status = VerifiedKnowledgeEligibilityStatus.INELIGIBLE_LOW_CONFIDENCE
        reason_codes.append("verified_candidate_low_confidence")
    elif source.assessment_explicit_abstention or source.synthesis_explicit_abstention:
        status = VerifiedKnowledgeEligibilityStatus.ABSTAINED
        reason_codes.append("verified_candidate_upstream_abstention")
    else:
        status = VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
        if source.candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE:
            reason_codes.append("verified_candidate_support_eligible")
        else:
            reason_codes.append("verified_candidate_refutation_eligible")
        reason_codes.append("verified_candidate_integrity_passed")

    eligible = status is VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_ELIGIBILITY_SCHEMA_VERSION,
        "candidate_kind": source.candidate_kind,
        "status": status,
        "eligible": eligible,
        "candidate_confidence_cap": cap,
        "operator_review_required": True,
        "automatic_promotion": False,
        "verified_knowledge_created": False,
        "cognitive_memory_written": False,
        "belief_mutated": False,
        "reason_codes": tuple(dict.fromkeys(reason_codes)),
        "runtime_effect": False,
    }
    return VerifiedKnowledgeEligibilityDecision.model_validate(
        {**payload, "decision_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_verified_knowledge_candidate(
    *,
    eligibility_input: VerifiedKnowledgeCandidateEligibilityInput,
    eligibility_decision: VerifiedKnowledgeEligibilityDecision | None = None,
    candidate_version: int = 1,
    lifecycle_status: VerifiedKnowledgeLifecycleStatus | None = None,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
    revalidation_due_at: datetime | None = None,
    supersedes_candidate_version_id: str | None = None,
    unresolved_dissent_ids: tuple[str, ...] = (),
) -> VerifiedKnowledgeCandidate:
    """Build an immutable reviewable candidate from explicit eligibility input."""

    decision = eligibility_decision or evaluate_verified_knowledge_candidate_eligibility(
        eligibility_input
    )
    lineage = eligibility_input.integrated_lineage
    identity_id = candidate_identity_id(
        candidate_kind=eligibility_input.candidate_kind,
        claim_identity_fingerprint=lineage.claim_identity_fingerprint,
        target_valid_time_fingerprint=lineage.target_valid_time_fingerprint,
        jurisdiction_scope_fingerprint=lineage.jurisdiction_scope_fingerprint,
        version_scope_fingerprint=lineage.version_scope_fingerprint,
    )
    identity_digest = identity_id.removeprefix("candidate-identity-")
    candidate_id = f"candidate-{identity_digest}-v{candidate_version:03d}"
    status = lifecycle_status or (
        VerifiedKnowledgeLifecycleStatus.OPERATOR_REVIEW_PENDING
        if decision.eligible
        else VerifiedKnowledgeLifecycleStatus.REVALIDATION_REQUIRED
    )
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "candidate_identity_id": identity_id,
        "candidate_kind": eligibility_input.candidate_kind,
        "claim_id": lineage.claim_id,
        "claim_identity_fingerprint": lineage.claim_identity_fingerprint,
        "integrated_lineage": lineage,
        "eligibility_decision": decision,
        "assessment_id": lineage.assessment_id,
        "assessment_status": eligibility_input.assessment_status,
        "assessment_confidence": quantize_confidence(eligibility_input.assessment_confidence),
        "assessment_confidence_band": _band(eligibility_input.assessment_confidence),
        "assessment_hard_cap": quantize_confidence(eligibility_input.assessment_hard_cap),
        "independent_support_count": eligibility_input.independent_support_count,
        "independent_opposition_count": eligibility_input.independent_opposition_count,
        "evidence_coverage": quantize_confidence(eligibility_input.evidence_coverage),
        "citation_coverage": quantize_confidence(eligibility_input.citation_coverage),
        "provenance_completeness": quantize_confidence(
            eligibility_input.provenance_completeness
        ),
        "freshness_status": eligibility_input.freshness_status,
        "scope_applicability_status": eligibility_input.scope_applicability_status,
        "contradiction_status": eligibility_input.contradiction_status,
        "mesh_session_id": lineage.domain_mesh_session_id,
        "synthesis_id": lineage.synthesis_id,
        "synthesis_fingerprint": lineage.synthesis_fingerprint,
        "synthesis_confidence_cap": quantize_confidence(lineage.synthesis_confidence_cap),
        "unresolved_dissent_ids": tuple(sorted(unresolved_dissent_ids)),
        "tool_verification_session_ids": lineage.tool_verification_session_ids,
        "attestation_chain_head_fingerprints": lineage.attestation_chain_head_fingerprints,
        "candidate_confidence_cap": decision.candidate_confidence_cap,
        "lifecycle_status": status,
        "candidate_version": candidate_version,
        "supersedes_candidate_version_id": supersedes_candidate_version_id,
        "created_at": created_at or utc_now(),
        "expires_at": expires_at,
        "revalidation_due_at": revalidation_due_at,
        "reason_codes": decision.reason_codes,
        "synthetic": lineage.synthetic,
        "read_only": True,
        "redacted": True,
        "operator_review_required": True,
        "automatic_promotion": False,
        "verified_knowledge_created": False,
        "persistent_write_applied": False,
        "cognitive_memory_written": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeCandidate.model_validate(
        {**payload, "candidate_fingerprint": verified_knowledge_fingerprint(payload)}
    )
