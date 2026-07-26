from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from aion_brain.contracts.knowledge_epistemic_assessment import (
    ContradictionStatus,
    EpistemicAssessmentStatus,
    FreshnessStatus,
    ScopeApplicability,
)
from aion_brain.contracts.knowledge_verified_memory import (
    EngagementSignalKind,
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateEligibilityInput,
    VerifiedKnowledgeCandidateKind,
    VerifiedKnowledgeCandidateVersion,
    verified_knowledge_fingerprint,
)
from aion_brain.knowledge_intelligence.engagement_signal_policy import (
    build_engagement_signal,
    build_engagement_signal_batch,
)
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    build_verified_knowledge_candidate,
    evaluate_verified_knowledge_candidate_eligibility,
)
from aion_brain.knowledge_intelligence.verified_knowledge_lineage import (
    build_integrated_knowledge_lineage,
)
from aion_brain.knowledge_intelligence.verified_knowledge_memory import (
    InMemoryVerifiedKnowledgeCandidateRepository,
)
from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
    create_candidate_version,
)

FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def fp(seed: str) -> str:
    return verified_knowledge_fingerprint({"seed": seed})


def sample_lineage(
    *,
    suffix: str = "001",
    status: EpistemicAssessmentStatus = EpistemicAssessmentStatus.SUPPORTED,
    assessment_confidence: Decimal = Decimal("0.910000"),
    assessment_hard_cap: Decimal = Decimal("0.900000"),
    synthesis_confidence_cap: Decimal = Decimal("0.890000"),
    tool_cap: Decimal = Decimal("0.880000"),
    claim_seed: str = "claim",
    scope_seed: str = "version",
):
    return build_integrated_knowledge_lineage(
        lineage_id=f"lineage-{suffix}",
        research_plan_id=f"research-plan-{suffix}",
        research_plan_fingerprint=fp(f"research-plan-{suffix}"),
        acquisition_result_fingerprint=fp(f"acquisition-{suffix}"),
        source_snapshot_ids=(f"snapshot-{suffix}",),
        source_snapshot_fingerprints=(fp(f"snapshot-{suffix}"),),
        source_provenance_ids=(f"provenance-{suffix}",),
        source_provenance_fingerprints=(fp(f"provenance-{suffix}"),),
        citation_reference_ids=(f"citation-{suffix}",),
        citation_reference_fingerprints=(fp(f"citation-{suffix}"),),
        source_registry_integrity_fingerprint=fp(f"registry-{suffix}"),
        claim_id=f"claim-{suffix}",
        claim_identity_fingerprint=fp(claim_seed),
        claim_version_id=f"claim-version-{suffix}",
        claim_graph_integrity_fingerprint=fp(f"claim-graph-{suffix}"),
        assessment_id=f"assessment-{suffix}",
        assessment_fingerprint=fp(f"assessment-{suffix}"),
        assessment_status=status,
        assessment_confidence=assessment_confidence,
        assessment_hard_cap=assessment_hard_cap,
        domain_mesh_session_id=f"mesh-session-{suffix}",
        domain_mesh_session_fingerprint=fp(f"mesh-session-{suffix}"),
        synthesis_id=f"synthesis-{suffix}",
        synthesis_fingerprint=fp(f"synthesis-{suffix}"),
        synthesis_confidence_cap=synthesis_confidence_cap,
        tool_verification_session_ids=(f"tool-session-{suffix}",),
        tool_verification_session_fingerprints=(fp(f"tool-session-{suffix}"),),
        attestation_chain_head_fingerprints=(fp(f"attestation-{suffix}"),),
        tool_evidence_confidence_caps=(tool_cap,),
        source_independence_group_ids=("group-001", "group-002", "group-003"),
        target_valid_time_fingerprint=fp("valid-time"),
        jurisdiction_scope_fingerprint=fp("jurisdiction"),
        version_scope_fingerprint=fp(scope_seed),
    )


def sample_eligibility_input(
    *,
    candidate_kind: VerifiedKnowledgeCandidateKind = (
        VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
    ),
    suffix: str = "001",
    **overrides: Any,
) -> VerifiedKnowledgeCandidateEligibilityInput:
    status = (
        EpistemicAssessmentStatus.SUPPORTED
        if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
        else EpistemicAssessmentStatus.CONTRADICTED
    )
    lineage = overrides.pop("integrated_lineage", None) or sample_lineage(
        suffix=suffix,
        status=status,
        assessment_confidence=overrides.get(
            "assessment_confidence", Decimal("0.910000")
        ),
        assessment_hard_cap=overrides.get("assessment_hard_cap", Decimal("0.900000")),
        synthesis_confidence_cap=overrides.get(
            "synthesis_confidence_cap", Decimal("0.890000")
        ),
        tool_cap=overrides.get("tool_evidence_confidence_caps", (Decimal("0.880000"),))[0],
        claim_seed=overrides.pop("claim_seed", "claim"),
        scope_seed=overrides.pop("scope_seed", "version"),
    )
    payload: dict[str, object] = {
        "candidate_kind": candidate_kind,
        "integrated_lineage": lineage,
        "source_registry_integrity_passed": True,
        "claim_graph_integrity_passed": True,
        "epistemic_assessment_integrity_passed": True,
        "domain_mesh_integrity_passed": True,
        "tool_verification_integrity_passed": True,
        "assessment_status": status,
        "assessment_explicit_abstention": False,
        "assessment_confidence": lineage.assessment_confidence,
        "assessment_hard_cap": lineage.assessment_hard_cap,
        "independent_support_count": (
            3 if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE else 0
        ),
        "independent_opposition_count": (
            3 if candidate_kind is VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE else 0
        ),
        "evidence_coverage": Decimal("1.000000"),
        "citation_coverage": Decimal("1.000000"),
        "provenance_completeness": Decimal("1.000000"),
        "freshness_status": FreshnessStatus.CURRENT,
        "scope_applicability_status": ScopeApplicability.APPLICABLE,
        "contradiction_status": ContradictionStatus.NONE_DETECTED,
        "retraction_applicable": False,
        "supersession_applicable": False,
        "current_evidence_after_supersession": False,
        "unresolved_material_support_conflict": False,
        "unresolved_material_opposition_conflict": False,
        "required_mesh_roles_complete": True,
        "unresolved_material_dissent": False,
        "required_report_confidence_caps": (Decimal("0.870000"),),
        "synthesis_explicit_abstention": False,
        "synthesis_confidence_cap": lineage.synthesis_confidence_cap,
        "tool_verification_session_count": 1,
        "tool_verification_statuses": ("simulation-passed",),
        "tool_evidence_confidence_caps": lineage.tool_evidence_confidence_caps,
        "tool_attestation_chains_valid": True,
        "actual_tool_executed": False,
        "engagement_signal_count": 0,
    }
    payload.update(overrides)
    return VerifiedKnowledgeCandidateEligibilityInput.model_validate(payload)


def sample_candidate(
    *,
    candidate_kind: VerifiedKnowledgeCandidateKind = (
        VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
    ),
    suffix: str = "001",
    **overrides: Any,
) -> VerifiedKnowledgeCandidate:
    source = sample_eligibility_input(
        candidate_kind=candidate_kind,
        suffix=suffix,
        **overrides,
    )
    decision = evaluate_verified_knowledge_candidate_eligibility(source)
    return build_verified_knowledge_candidate(
        eligibility_input=source,
        eligibility_decision=decision,
        created_at=FIXED_TIME,
    )


def sample_version(
    *,
    candidate_kind: VerifiedKnowledgeCandidateKind = (
        VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
    ),
    suffix: str = "001",
    **overrides: Any,
) -> VerifiedKnowledgeCandidateVersion:
    return create_candidate_version(
        sample_candidate(candidate_kind=candidate_kind, suffix=suffix, **overrides),
        created_at=FIXED_TIME,
    )


def sample_repository() -> InMemoryVerifiedKnowledgeCandidateRepository:
    return InMemoryVerifiedKnowledgeCandidateRepository().with_candidate_version(sample_version())


def sample_signal(
    *,
    signal_id: str = "signal-001",
    signal_kind: EngagementSignalKind = EngagementSignalKind.QUERY_REPEATED,
    outcome: str = "unresolved-query",
    metadata_codes: tuple[str, ...] = (),
):
    return build_engagement_signal(
        signal_id=signal_id,
        signal_kind=signal_kind,
        session_fingerprint=fp(f"session-{signal_id}"),
        response_fingerprint=fp(f"response-{signal_id}"),
        subject_fingerprint=fp(f"subject-{signal_id}"),
        bounded_outcome_code=outcome,
        metadata_codes=metadata_codes,
        occurred_at=FIXED_TIME,
    )


def sample_signal_batch():
    return build_engagement_signal_batch(
        batch_id="engagement-signals-001",
        signals=(sample_signal(),),
    )
