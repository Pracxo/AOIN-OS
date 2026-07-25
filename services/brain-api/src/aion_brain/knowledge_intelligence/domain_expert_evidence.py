"""Redacted evidence and operator-review helpers for the domain expert mesh."""

from __future__ import annotations

from datetime import timedelta
from typing import Literal

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    CaseRiskClass,
    DomainExpertMeshDiagnostics,
    DomainExpertMeshEvidenceBundle,
    DomainExpertMeshIncidentRecord,
    DomainExpertMeshIntegrityReport,
    DomainExpertMeshOperatorReviewItem,
    ExpertDisagreementMatrix,
    ExpertMeshSynthesis,
    ExpertPanelPlan,
    ExpertPerspectiveReport,
    MeshIntegrityStatus,
    domain_expert_mesh_diagnostics_fingerprint,
    domain_expert_mesh_evidence_bundle_fingerprint,
    domain_expert_mesh_incident_fingerprint,
    domain_expert_mesh_operator_review_fingerprint,
)
from aion_brain.contracts.knowledge_research import utc_now


def build_mesh_incident(
    *,
    incident_id: str,
    reason_codes: tuple[str, ...],
    severity: Literal["low", "medium", "high", "critical"] = "medium",
    redacted_summary: str = "Domain expert mesh incident requires operator review",
    clock: object = utc_now,
) -> DomainExpertMeshIncidentRecord:
    """Build a safe incident record without source text or exception details."""

    now = clock() if callable(clock) else utc_now()
    payload = {
        "incident_id": incident_id,
        "reason_codes": reason_codes,
        "severity": severity,
        "redacted_summary": redacted_summary,
        "created_at": now,
    }
    return DomainExpertMeshIncidentRecord.model_validate(
        {**payload, "incident_fingerprint": domain_expert_mesh_incident_fingerprint(payload)}
    )


def build_operator_review_item(
    *,
    session_id: str,
    case_id: str,
    reason_codes: tuple[str, ...],
    clock: object = utc_now,
) -> DomainExpertMeshOperatorReviewItem:
    """Build the mandatory human review evidence item."""

    now = clock() if callable(clock) else utc_now()
    payload = {
        "review_item_id": f"review-{session_id}",
        "session_id": session_id,
        "case_id": case_id,
        "reason_codes": reason_codes or ("domain_mesh_operator_review_required",),
        "created_at": now,
        "expires_at": now + timedelta(days=7),
    }
    return DomainExpertMeshOperatorReviewItem.model_validate(
        {**payload, "review_fingerprint": domain_expert_mesh_operator_review_fingerprint(payload)}
    )


def build_mesh_diagnostics(
    *,
    session_id: str,
    case_risk_class: CaseRiskClass,
    panel_plan: ExpertPanelPlan,
    reports: tuple[ExpertPerspectiveReport, ...],
    matrix: ExpertDisagreementMatrix,
    synthesis: ExpertMeshSynthesis,
    integrity_report: DomainExpertMeshIntegrityReport | None = None,
) -> DomainExpertMeshDiagnostics:
    """Build redacted diagnostics from IDs, counts, positions, and caps only."""

    role_counts: dict[str, int] = {}
    for assignment in panel_plan.assignments:
        role_counts[assignment.perspective_role.value] = (
            role_counts.get(assignment.perspective_role.value, 0) + 1
        )
    domain_counts: dict[str, int] = {}
    position_counts: dict[str, int] = {}
    for report in reports:
        position_counts[report.position.value] = position_counts.get(report.position.value, 0) + 1
    disagreement_counts: dict[str, int] = {}
    for item in matrix.disagreements:
        disagreement_counts[item.disagreement_type.value] = (
            disagreement_counts.get(item.disagreement_type.value, 0) + 1
        )
    status = integrity_report.status if integrity_report is not None else MeshIntegrityStatus.PASSED
    payload = {
        "session_id": session_id,
        "role_counts": role_counts,
        "domain_counts": domain_counts,
        "risk_class": case_risk_class,
        "position_counts": position_counts,
        "alignment_state": synthesis.alignment_state,
        "disagreement_counts": disagreement_counts,
        "confidence_caps": tuple(report.report_confidence_cap for report in reports)
        + (synthesis.synthesis_confidence_cap,),
        "explicit_abstention": synthesis.explicit_abstention,
        "integrity_status": status,
        "reason_codes": synthesis.synthesis_codes,
    }
    return DomainExpertMeshDiagnostics.model_validate(
        {**payload, "diagnostics_fingerprint": domain_expert_mesh_diagnostics_fingerprint(payload)}
    )


def build_mesh_evidence_bundle(
    *,
    session_id: str,
    case_id: str,
    domain_ids: tuple[str, ...],
    specialty_ids: tuple[str, ...],
    risk_class: CaseRiskClass,
    panel_plan: ExpertPanelPlan,
    reports: tuple[ExpertPerspectiveReport, ...],
    matrix: ExpertDisagreementMatrix,
    synthesis: ExpertMeshSynthesis,
    integrity_report: DomainExpertMeshIntegrityReport,
) -> DomainExpertMeshEvidenceBundle:
    """Build safe operator-review evidence from IDs, counts, and fingerprints only."""

    payload = {
        "session_id": session_id,
        "case_id": case_id,
        "fingerprints": tuple(
            sorted(
                {
                    panel_plan.panel_fingerprint,
                    matrix.matrix_fingerprint,
                    synthesis.synthesis_fingerprint,
                    integrity_report.report_fingerprint,
                    *(report.report_fingerprint for report in reports),
                }
            )
        ),
        "counts": {
            "reports": len(reports),
            "critiques": len(matrix.preserved_critique_ids),
            "disagreements": matrix.disagreement_count,
            "panel": panel_plan.panel_size,
        },
        "role_ids": tuple(
            sorted(
                {item.perspective_role for item in panel_plan.assignments},
                key=lambda role: role.value,
            )
        ),
        "domain_ids": domain_ids,
        "specialty_ids": specialty_ids,
        "risk_class": risk_class,
        "positions": tuple(
            sorted({report.position for report in reports}, key=lambda item: item.value)
        ),
        "alignment_state": synthesis.alignment_state,
        "disagreement_types": tuple(
            sorted(
                {item.disagreement_type for item in matrix.disagreements},
                key=lambda item: item.value,
            )
        ),
        "confidence_caps": tuple(report.report_confidence_cap for report in reports)
        + (synthesis.synthesis_confidence_cap,),
        "explicit_abstention": synthesis.explicit_abstention,
        "integrity_status": integrity_report.status,
    }
    return DomainExpertMeshEvidenceBundle.model_validate(
        {**payload, "evidence_fingerprint": domain_expert_mesh_evidence_bundle_fingerprint(payload)}
    )


__all__ = [
    "build_mesh_diagnostics",
    "build_mesh_evidence_bundle",
    "build_mesh_incident",
    "build_operator_review_item",
]
