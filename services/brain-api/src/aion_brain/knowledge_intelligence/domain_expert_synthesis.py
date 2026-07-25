"""Deterministic advisory synthesis for the domain expert mesh."""

from __future__ import annotations

from decimal import Decimal

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    CaseRiskClass,
    DomainExpertCase,
    ExpertCritique,
    ExpertDisagreementMatrix,
    ExpertMeshSynthesis,
    ExpertPanelPlan,
    ExpertPerspectiveReport,
    ExpertReportPosition,
    PanelAlignmentState,
    expert_mesh_synthesis_fingerprint,
)


def _alignment_state(
    reports: tuple[ExpertPerspectiveReport, ...],
    matrix: ExpertDisagreementMatrix,
    *,
    explicit_abstention: bool,
) -> PanelAlignmentState:
    if not reports:
        return PanelAlignmentState.ABSTAIN
    if matrix.disagreement_count:
        return PanelAlignmentState.UNRESOLVED_DISAGREEMENT
    if explicit_abstention:
        return PanelAlignmentState.ABSTAIN
    positions = {report.position for report in reports}
    if len(positions) == 1:
        return PanelAlignmentState.UNANIMOUS_ALIGNMENT
    if ExpertReportPosition.MIXED in positions:
        return PanelAlignmentState.QUALIFIED_ALIGNMENT
    return PanelAlignmentState.PLURAL_POSITIONS


def synthesize_expert_mesh(
    case: DomainExpertCase,
    panel_plan: ExpertPanelPlan,
    reports: tuple[ExpertPerspectiveReport, ...],
    critiques: tuple[ExpertCritique, ...],
    matrix: ExpertDisagreementMatrix,
) -> ExpertMeshSynthesis:
    """Create a bounded advisory synthesis without truth or confidence amplification."""

    high_stakes = case.risk_class in {CaseRiskClass.HIGH, CaseRiskClass.CRITICAL}
    missing_required = bool(panel_plan.missing_required_roles)
    evidence_gap = any(report.evidence_gap_codes for report in reports)
    explicit_abstention = (
        high_stakes
        or missing_required
        or evidence_gap
        or matrix.disagreement_count > 0
        or any(report.explicit_abstention for report in reports)
    )
    underlying_cap = min(
        (report.underlying_assessment_confidence_cap for report in reports),
        default=Decimal("0.000000"),
    )
    report_cap = min(
        (report.report_confidence_cap for report in reports), default=Decimal("0.000000")
    )
    synthesis_cap = min(underlying_cap, report_cap)
    if matrix.disagreement_count:
        synthesis_cap = min(synthesis_cap, Decimal("0.650000"))
    if explicit_abstention:
        synthesis_cap = min(synthesis_cap, Decimal("0.650000"))
    alignment = _alignment_state(reports, matrix, explicit_abstention=explicit_abstention)
    codes = [
        "domain_mesh_underlying_cap_propagated",
        "domain_mesh_confidence_non_amplification_enforced",
    ]
    if alignment == PanelAlignmentState.UNANIMOUS_ALIGNMENT:
        codes.append("domain_mesh_alignment_unanimous")
    elif alignment == PanelAlignmentState.QUALIFIED_ALIGNMENT:
        codes.append("domain_mesh_alignment_qualified")
    elif alignment == PanelAlignmentState.PLURAL_POSITIONS:
        codes.append("domain_mesh_alignment_plural")
    elif alignment == PanelAlignmentState.UNRESOLVED_DISAGREEMENT:
        codes.append("domain_mesh_alignment_unresolved")
    else:
        codes.append("domain_mesh_alignment_abstain")
    if high_stakes:
        codes.append("domain_mesh_high_stakes_abstention")
    if explicit_abstention:
        codes.append("domain_mesh_operator_review_required")
    if matrix.disagreement_count:
        codes.append("domain_mesh_dissent_preserved")

    payload = {
        "synthesis_id": f"synthesis-{case.case_id}",
        "case_id": case.case_id,
        "panel_id": panel_plan.panel_id,
        "report_ids": tuple(sorted(report.report_id for report in reports)),
        "critique_ids": tuple(sorted(critique.critique_id for critique in critiques)),
        "disagreement_ids": tuple(sorted(item.disagreement_id for item in matrix.disagreements)),
        "alignment_state": alignment,
        "synthesis_codes": tuple(dict.fromkeys(codes)),
        "evidence_gap_codes": tuple(
            sorted({code for report in reports for code in report.evidence_gap_codes})
        ),
        "unresolved_dissent_ids": tuple(
            sorted(item.disagreement_id for item in matrix.disagreements if item.material)
        ),
        "underlying_assessment_confidence_cap": underlying_cap,
        "report_confidence_cap": report_cap,
        "synthesis_confidence_cap": synthesis_cap,
        "explicit_abstention": explicit_abstention,
        "operator_review_required": explicit_abstention,
        "operator_escalation_recommended": high_stakes or bool(matrix.disagreement_count),
    }
    return ExpertMeshSynthesis.model_validate(
        {**payload, "synthesis_fingerprint": expert_mesh_synthesis_fingerprint(payload)}
    )


__all__ = ["synthesize_expert_mesh"]
