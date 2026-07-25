"""Deterministic expert reports, critiques, and disagreement detection."""

from __future__ import annotations

from decimal import Decimal

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    CaseRiskClass,
    DisagreementType,
    DomainExpertCase,
    ExpertCritique,
    ExpertCritiqueResponse,
    ExpertDisagreementItem,
    ExpertDisagreementMatrix,
    ExpertPanelPlan,
    ExpertPerspectiveReport,
    ExpertPerspectiveRole,
    ExpertReportPosition,
    assessment_position,
    expert_critique_fingerprint,
    expert_critique_response_fingerprint,
    expert_disagreement_item_fingerprint,
    expert_disagreement_matrix_fingerprint,
    expert_perspective_report_fingerprint,
)
from aion_brain.contracts.knowledge_epistemic_assessment import (
    ClaimEpistemicAssessment,
    EpistemicAssessmentStatus,
)


def _assessment_index(
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> dict[str, ClaimEpistemicAssessment]:
    return {assessment.assessment_id: assessment for assessment in assessments}


def _case_assessments(
    case: DomainExpertCase,
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> tuple[ClaimEpistemicAssessment, ...]:
    by_id = _assessment_index(assessments)
    missing = [item for item in case.epistemic_assessment_ids if item not in by_id]
    if missing:
        raise ValueError("domain expert mesh assessment reference unresolved")
    return tuple(by_id[item] for item in case.epistemic_assessment_ids)


def _underlying_cap(assessments: tuple[ClaimEpistemicAssessment, ...]) -> Decimal:
    if not assessments:
        return Decimal("0.000000")
    return min(assessment.confidence for assessment in assessments)


def _position_for_role(
    role: ExpertPerspectiveRole,
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> ExpertReportPosition:
    statuses = {assessment.status for assessment in assessments}
    if not statuses:
        return ExpertReportPosition.ABSTAIN
    if role == ExpertPerspectiveRole.EVIDENCE_AUDITOR and any(
        item in statuses
        for item in {
            EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE,
            EpistemicAssessmentStatus.UNKNOWN,
        }
    ):
        return ExpertReportPosition.INSUFFICIENT_EVIDENCE
    if role == ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC and len(statuses) > 1:
        return ExpertReportPosition.MIXED
    if len(statuses) == 1:
        return assessment_position(next(iter(statuses)))
    return ExpertReportPosition.MIXED


def _finding_codes(
    role: ExpertPerspectiveRole,
    position: ExpertReportPosition,
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> tuple[str, ...]:
    codes: list[str] = [
        "domain_mesh_report_created",
        "domain_mesh_assessment_reference_resolved",
        "domain_mesh_underlying_cap_propagated",
        "domain_mesh_confidence_non_amplification_enforced",
    ]
    if role == ExpertPerspectiveRole.EVIDENCE_AUDITOR:
        codes.append("domain_mesh_evidence_reference_resolved")
    if role == ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC:
        codes.extend(("domain_mesh_assumption_recorded", "domain_mesh_limitation_recorded"))
    if position in {
        ExpertReportPosition.INSUFFICIENT_EVIDENCE,
        ExpertReportPosition.UNKNOWN,
        ExpertReportPosition.ABSTAIN,
    } or any(item.explicit_abstention for item in assessments):
        codes.append("domain_mesh_evidence_gap_recorded")
    return tuple(dict.fromkeys(codes))


def _evidence_references(assessments: tuple[ClaimEpistemicAssessment, ...]) -> tuple[str, ...]:
    refs: list[str] = []
    for assessment in assessments:
        refs.extend(assessment.structural_conflict_candidate_ids)
        refs.extend(assessment.applicable_correction_relation_ids)
        refs.extend(assessment.applicable_retraction_relation_ids)
        refs.extend(assessment.applicable_supersession_relation_ids)
    return tuple(sorted(dict.fromkeys(refs)))


def generate_expert_reports(
    case: DomainExpertCase,
    panel_plan: ExpertPanelPlan,
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> tuple[ExpertPerspectiveReport, ...]:
    """Generate immutable reports from existing assessment metadata."""

    case_assessments = _case_assessments(case, assessments)
    cap = _underlying_cap(case_assessments)
    high_stakes = case.risk_class in {CaseRiskClass.HIGH, CaseRiskClass.CRITICAL}
    reports: list[ExpertPerspectiveReport] = []
    for assignment in panel_plan.assignments:
        position = _position_for_role(assignment.perspective_role, case_assessments)
        explicit_abstention = (
            panel_plan.explicit_abstention_required
            or high_stakes
            or any(assessment.explicit_abstention for assessment in case_assessments)
            or position
            in {ExpertReportPosition.INSUFFICIENT_EVIDENCE, ExpertReportPosition.ABSTAIN}
        )
        finding_codes = _finding_codes(assignment.perspective_role, position, case_assessments)
        assumption_codes = (
            ("domain_mesh_assumption_recorded",)
            if assignment.perspective_role == ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC
            else ()
        )
        limitation_codes = (
            ("domain_mesh_limitation_recorded",)
            if explicit_abstention
            or assignment.perspective_role
            in {
                ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC,
                ExpertPerspectiveRole.RISK_REVIEWER,
            }
            else ()
        )
        gap_codes = (
            ("domain_mesh_evidence_gap_recorded",)
            if explicit_abstention
            or position
            in {ExpertReportPosition.INSUFFICIENT_EVIDENCE, ExpertReportPosition.UNKNOWN}
            else ()
        )
        report_cap = min(cap, Decimal("0.650000")) if explicit_abstention else cap
        payload = {
            "report_id": f"report-{case.case_id}-{assignment.perspective_role.value}",
            "case_id": case.case_id,
            "panel_id": panel_plan.panel_id,
            "profile_id": assignment.profile_id,
            "assignment_id": assignment.assignment_id,
            "perspective_role": assignment.perspective_role,
            "claim_ids": case.claim_ids,
            "assessment_ids": tuple(assessment.assessment_id for assessment in case_assessments),
            "evidence_reference_ids": _evidence_references(case_assessments),
            "finding_codes": finding_codes,
            "assumption_codes": assumption_codes,
            "limitation_codes": limitation_codes,
            "evidence_gap_codes": gap_codes,
            "position": ExpertReportPosition.ABSTAIN if explicit_abstention else position,
            "underlying_assessment_confidence_cap": cap,
            "report_confidence_cap": report_cap,
            "explicit_abstention": explicit_abstention,
        }
        reports.append(
            ExpertPerspectiveReport.model_validate(
                {**payload, "report_fingerprint": expert_perspective_report_fingerprint(payload)}
            )
        )
    return tuple(sorted(reports, key=lambda item: item.report_id))


def generate_expert_critiques(
    reports: tuple[ExpertPerspectiveReport, ...],
    *,
    deliberation_round: int = 1,
) -> tuple[ExpertCritique, ...]:
    """Generate deterministic cross-examination critiques without self-review."""

    critiques: list[ExpertCritique] = []
    ordered_reports = tuple(sorted(reports, key=lambda item: item.report_id))
    for index, target in enumerate(ordered_reports):
        critic_candidates = [
            item
            for item in ordered_reports
            if item.profile_id != target.profile_id
            and item.perspective_role != ExpertPerspectiveRole.SYNTHESIS_COORDINATOR
        ]
        if not critic_candidates:
            continue
        critic = critic_candidates[index % len(critic_candidates)]
        issue_codes = ["domain_mesh_critique_created"]
        if critic.position != target.position:
            issue_codes.append("domain_mesh_disagreement_detected")
        if target.evidence_gap_codes:
            issue_codes.append("domain_mesh_evidence_gap_recorded")
        if target.limitation_codes:
            issue_codes.append("domain_mesh_limitation_recorded")
        payload = {
            "critique_id": f"critique-{target.report_id}-{critic.perspective_role.value}",
            "case_id": target.case_id,
            "panel_id": target.panel_id,
            "critic_profile_id": critic.profile_id,
            "target_profile_id": target.profile_id,
            "target_report_id": target.report_id,
            "deliberation_round": deliberation_round,
            "issue_codes": tuple(dict.fromkeys(issue_codes)),
            "unsupported_reference_ids": (),
            "methodology_issue_codes": (
                ("domain_mesh_limitation_recorded",) if target.limitation_codes else ()
            ),
            "scope_issue_codes": (
                ("domain_mesh_evidence_gap_recorded",) if target.evidence_gap_codes else ()
            ),
        }
        critiques.append(
            ExpertCritique.model_validate(
                {**payload, "critique_fingerprint": expert_critique_fingerprint(payload)}
            )
        )
    return tuple(sorted(critiques, key=lambda item: item.critique_id))


def generate_expert_critique_responses(
    critiques: tuple[ExpertCritique, ...],
) -> tuple[ExpertCritiqueResponse, ...]:
    """Generate deterministic responses without deleting critiques."""

    responses: list[ExpertCritiqueResponse] = []
    for critique in sorted(critiques, key=lambda item: item.critique_id):
        retained = "domain_mesh_disagreement_detected" in critique.issue_codes
        payload = {
            "response_id": f"response-{critique.critique_id}",
            "critique_id": critique.critique_id,
            "respondent_profile_id": critique.target_profile_id,
            "response_code": "retain_disagreement" if retained else "acknowledge",
            "retained_disagreement": retained,
        }
        responses.append(
            ExpertCritiqueResponse.model_validate(
                {
                    **payload,
                    "response_fingerprint": expert_critique_response_fingerprint(payload),
                }
            )
        )
    return tuple(responses)


def build_disagreement_matrix(
    case: DomainExpertCase,
    panel_plan: ExpertPanelPlan,
    reports: tuple[ExpertPerspectiveReport, ...],
    critiques: tuple[ExpertCritique, ...],
) -> ExpertDisagreementMatrix:
    """Build a deterministic matrix while preserving minority reports."""

    items: list[ExpertDisagreementItem] = []
    report_ids = tuple(sorted(report.report_id for report in reports))
    critique_ids = tuple(sorted(critique.critique_id for critique in critiques))
    positions = tuple(sorted({report.position for report in reports}, key=lambda item: item.value))
    if len(positions) > 1:
        payload = {
            "disagreement_id": f"disagreement-{case.case_id}-position",
            "disagreement_type": DisagreementType.POSITION,
            "report_ids": report_ids,
            "critique_ids": critique_ids,
            "position_values": positions,
            "reason_codes": (
                "domain_mesh_disagreement_detected",
                "domain_mesh_dissent_preserved",
            ),
            "material": True,
        }
        items.append(
            ExpertDisagreementItem.model_validate(
                {
                    **payload,
                    "disagreement_fingerprint": expert_disagreement_item_fingerprint(payload),
                }
            )
        )
    evidence_sets = {report.evidence_reference_ids for report in reports}
    if len(evidence_sets) > 1 or any(report.evidence_gap_codes for report in reports):
        payload = {
            "disagreement_id": f"disagreement-{case.case_id}-evidence",
            "disagreement_type": DisagreementType.EVIDENCE,
            "report_ids": report_ids,
            "critique_ids": critique_ids,
            "position_values": positions,
            "reason_codes": (
                "domain_mesh_disagreement_detected",
                "domain_mesh_evidence_gap_recorded",
                "domain_mesh_dissent_preserved",
            ),
            "material": True,
        }
        items.append(
            ExpertDisagreementItem.model_validate(
                {
                    **payload,
                    "disagreement_fingerprint": expert_disagreement_item_fingerprint(payload),
                }
            )
        )
    cap_values = {report.report_confidence_cap for report in reports}
    if len(cap_values) > 1:
        payload = {
            "disagreement_id": f"disagreement-{case.case_id}-confidence-cap",
            "disagreement_type": DisagreementType.CONFIDENCE_CAP,
            "report_ids": report_ids,
            "critique_ids": critique_ids,
            "position_values": positions,
            "reason_codes": (
                "domain_mesh_disagreement_detected",
                "domain_mesh_underlying_cap_propagated",
                "domain_mesh_confidence_non_amplification_enforced",
            ),
            "material": True,
        }
        items.append(
            ExpertDisagreementItem.model_validate(
                {
                    **payload,
                    "disagreement_fingerprint": expert_disagreement_item_fingerprint(payload),
                }
            )
        )
    payload = {
        "matrix_id": f"matrix-{case.case_id}",
        "case_id": case.case_id,
        "panel_id": panel_plan.panel_id,
        "disagreements": tuple(sorted(items, key=lambda item: item.disagreement_id)),
        "disagreement_count": len(items),
        "preserved_report_ids": report_ids,
        "preserved_critique_ids": critique_ids,
    }
    return ExpertDisagreementMatrix.model_validate(
        {**payload, "matrix_fingerprint": expert_disagreement_matrix_fingerprint(payload)}
    )


__all__ = [
    "build_disagreement_matrix",
    "generate_expert_critique_responses",
    "generate_expert_critiques",
    "generate_expert_reports",
]
