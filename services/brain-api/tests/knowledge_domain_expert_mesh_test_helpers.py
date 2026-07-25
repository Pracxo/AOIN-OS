from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    CaseRiskClass,
    DomainExpertCase,
    domain_expert_case_fingerprint,
)
from aion_brain.contracts.knowledge_epistemic_assessment import (
    CLAIM_EPISTEMIC_ASSESSMENT_SCHEMA_VERSION,
    EPISTEMIC_SCORECARD_VERSION,
    ClaimEpistemicAssessment,
    ContradictionStatus,
    EpistemicAssessmentStatus,
    FreshnessStatus,
    ScopeApplicability,
    claim_epistemic_assessment_fingerprint,
    confidence_band_for,
    default_scorecard_policy,
)
from aion_brain.contracts.knowledge_research import fingerprint_payload
from aion_brain.knowledge_intelligence.domain_expert_mesh import ControlledDomainExpertMesh

MESH_TEST_NOW = datetime(2026, 1, 1, tzinfo=UTC)

STATUS_REASON_CODES = {
    EpistemicAssessmentStatus.SUPPORTED: "epistemic_status_supported",
    EpistemicAssessmentStatus.CONTRADICTED: "epistemic_status_contradicted",
    EpistemicAssessmentStatus.MIXED: "epistemic_status_mixed",
    EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE: "epistemic_status_insufficient",
    EpistemicAssessmentStatus.STALE: "epistemic_status_stale",
    EpistemicAssessmentStatus.SUPERSEDED: "epistemic_status_superseded",
    EpistemicAssessmentStatus.RETRACTED: "epistemic_status_retracted",
    EpistemicAssessmentStatus.SCOPE_MISMATCH: "epistemic_status_scope_mismatch",
    EpistemicAssessmentStatus.UNKNOWN: "epistemic_status_unknown",
}


def make_assessment(
    *,
    assessment_id: str = "assessment-001",
    claim_id: str = "claim-001",
    status: EpistemicAssessmentStatus = EpistemicAssessmentStatus.SUPPORTED,
    confidence: Decimal = Decimal("0.620000"),
    explicit_abstention: bool = False,
) -> ClaimEpistemicAssessment:
    payload = {
        "schema_version": CLAIM_EPISTEMIC_ASSESSMENT_SCHEMA_VERSION,
        "assessment_id": assessment_id,
        "request_id": "request-001",
        "claim_id": claim_id,
        "claim_identity_fingerprint": fingerprint_payload({"claim_id": claim_id}),
        "source_registry_integrity_fingerprint": fingerprint_payload({"registry": "ok"}),
        "claim_graph_integrity_fingerprint": fingerprint_payload({"graph": "ok"}),
        "assessment_policy_fingerprint": default_scorecard_policy().policy_fingerprint,
        "scorecard_version": EPISTEMIC_SCORECARD_VERSION,
        "status": status,
        "confidence": confidence,
        "confidence_band": confidence_band_for(confidence),
        "explicit_abstention": explicit_abstention,
        "independent_support_count": 2 if status == EpistemicAssessmentStatus.SUPPORTED else 0,
        "independent_opposition_count": 2
        if status == EpistemicAssessmentStatus.CONTRADICTED
        else 0,
        "duplicate_suppressed_count": 0,
        "mirror_suppressed_count": 0,
        "ambiguous_group_count": 0,
        "reference_resolution": Decimal("1.000000"),
        "evidence_coverage": Decimal("1.000000"),
        "citation_coverage": Decimal("1.000000"),
        "provenance_completeness": Decimal("1.000000"),
        "support_score": confidence
        if status == EpistemicAssessmentStatus.SUPPORTED
        else Decimal("0.000000"),
        "opposition_score": confidence
        if status == EpistemicAssessmentStatus.CONTRADICTED
        else Decimal("0.000000"),
        "freshness_status": FreshnessStatus.CURRENT,
        "scope_applicability": ScopeApplicability.APPLICABLE,
        "contradiction_status": ContradictionStatus.NONE_DETECTED,
        "applicable_correction_relation_ids": (),
        "applicable_retraction_relation_ids": (),
        "applicable_supersession_relation_ids": (),
        "structural_conflict_candidate_ids": ("conflict-001",),
        "hard_caps": (),
        "reason_codes": (STATUS_REASON_CODES[status],),
        "assessment_time": MESH_TEST_NOW,
        "unverified_source_inputs": True,
        "absolute_truth_claimed": False,
        "claim_accepted": False,
        "claim_rejected": False,
        "contradiction_resolved": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    payload["assessment_fingerprint"] = claim_epistemic_assessment_fingerprint(payload)
    return ClaimEpistemicAssessment.model_validate(payload)


def make_case(
    *,
    case_id: str = "case-001",
    claim_ids: tuple[str, ...] = ("claim-001",),
    assessment_ids: tuple[str, ...] = ("assessment-001",),
    domain_ids: tuple[str, ...] = ("computing-and-information-systems",),
    specialty_ids: tuple[str, ...] = ("computing-and-information-systems-general",),
    risk_class: CaseRiskClass = CaseRiskClass.HIGH,
    target_valid_time: datetime | None = MESH_TEST_NOW,
    target_jurisdiction_ids: tuple[str, ...] = ("us",),
    target_version_ids: tuple[str, ...] = ("current",),
) -> DomainExpertCase:
    payload = {
        "case_id": case_id,
        "question_summary": "Assess explicit claim posture for advisory review",
        "claim_ids": claim_ids,
        "epistemic_assessment_ids": assessment_ids,
        "domain_ids": domain_ids,
        "specialty_ids": specialty_ids,
        "target_valid_time": target_valid_time,
        "target_jurisdiction_ids": target_jurisdiction_ids,
        "target_version_ids": target_version_ids,
        "risk_class": risk_class,
        "synthetic": True,
    }
    payload["case_fingerprint"] = domain_expert_case_fingerprint(payload)
    return DomainExpertCase.model_validate(payload)


def run_sample_session():
    assessment = make_assessment()
    case = make_case()
    mesh = ControlledDomainExpertMesh(clock=lambda: MESH_TEST_NOW)
    return mesh, case, assessment, mesh.run_session(case=case, assessments=(assessment,))
