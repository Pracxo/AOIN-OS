"""Integrity audits for deterministic domain expert mesh artifacts."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    CaseRiskClass,
    DomainExpertMeshIntegrityFinding,
    DomainExpertMeshIntegrityReport,
    DomainExpertMeshSession,
    DomainExpertProfileRegistry,
    DomainTaxonomy,
    ExpertCritique,
    ExpertDisagreementMatrix,
    ExpertMeshSynthesis,
    ExpertPanelPlan,
    ExpertPerspectiveReport,
    MeshIntegrityStatus,
    domain_expert_mesh_integrity_report_fingerprint,
)
from aion_brain.contracts.knowledge_research import utc_now


def _finding(
    *,
    index: int,
    reason_code: str,
    summary: str,
    severity: str = "high",
    safe_ids: tuple[str, ...] = (),
    count: int | None = None,
) -> DomainExpertMeshIntegrityFinding:
    return DomainExpertMeshIntegrityFinding(
        finding_id=f"domain-mesh-finding-{index:03d}",
        severity=severity,  # type: ignore[arg-type]
        reason_codes=(reason_code,),
        safe_ids=safe_ids,
        bounded_count=count,
        redacted_summary=summary,
    )


def _report(
    report_id: str,
    findings: list[DomainExpertMeshIntegrityFinding],
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    now = clock() if callable(clock) else utc_now()
    if not isinstance(now, datetime):
        now = utc_now()
    status = MeshIntegrityStatus.FAILED if findings else MeshIntegrityStatus.PASSED
    reason_codes = (
        ("domain_mesh_integrity_failed",) if findings else ("domain_mesh_integrity_passed",)
    )
    payload = {
        "report_id": report_id,
        "status": status,
        "finding_count": len(findings),
        "findings": tuple(findings),
        "reason_codes": reason_codes,
        "audit_timestamp": now,
    }
    return DomainExpertMeshIntegrityReport.model_validate(
        {**payload, "report_fingerprint": domain_expert_mesh_integrity_report_fingerprint(payload)}
    )


def audit_domain_taxonomy(
    taxonomy: DomainTaxonomy,
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit deterministic taxonomy integrity."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    if len({node.domain_id for node in taxonomy.nodes}) != len(taxonomy.nodes):
        findings.append(
            _finding(
                index=1,
                reason_code="domain_mesh_taxonomy_cycle",
                summary="Duplicate taxonomy domain identifier detected",
            )
        )
    return _report("integrity-domain-taxonomy", findings, clock=clock)


def audit_expert_profile_registry(
    registry: DomainExpertProfileRegistry,
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit computational profile registry integrity."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    for profile in registry.profiles:
        if profile.human_identity_claimed or profile.human_expert_impersonation:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_human_identity_blocked",
                    summary="Profile human identity claim rejected",
                    safe_ids=(profile.profile_id,),
                )
            )
        if profile.professional_credential_claimed or profile.licensed_professional_claimed:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_professional_credential_blocked",
                    summary="Profile credential claim rejected",
                    safe_ids=(profile.profile_id,),
                )
            )
        if profile.model_provider_required:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_model_provider_blocked",
                    summary="Profile model-provider requirement rejected",
                    safe_ids=(profile.profile_id,),
                )
            )
        if profile.tool_execution_required:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_tool_execution_blocked",
                    summary="Profile tool execution requirement rejected",
                    safe_ids=(profile.profile_id,),
                )
            )
        if profile.network_access_required:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_network_blocked",
                    summary="Profile network requirement rejected",
                    safe_ids=(profile.profile_id,),
                )
            )
    return _report("integrity-expert-profile-registry", findings, clock=clock)


def audit_panel_plan(
    panel_plan: ExpertPanelPlan,
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit required roles and independence groups."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    if panel_plan.missing_required_roles:
        findings.append(
            _finding(
                index=1,
                reason_code="domain_mesh_required_role_missing",
                summary="Required panel role missing",
                count=len(panel_plan.missing_required_roles),
            )
        )
    if panel_plan.independence_group_count != panel_plan.panel_size:
        findings.append(
            _finding(
                index=len(findings) + 1,
                reason_code="domain_mesh_independence_group_duplicate",
                summary="Duplicate independence group detected",
            )
        )
    return _report(f"integrity-{panel_plan.panel_id}", findings, clock=clock)


def audit_expert_reports(
    reports: tuple[ExpertPerspectiveReport, ...],
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit report safety and confidence caps."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    for report in reports:
        if report.report_confidence_cap > report.underlying_assessment_confidence_cap:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_confidence_non_amplification_enforced",
                    summary="Report confidence cap exceeds underlying cap",
                    safe_ids=(report.report_id,),
                )
            )
        if (
            report.truth_decision
            or report.claim_accepted
            or report.claim_rejected
            or report.automatic_action
        ):
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_absolute_truth_blocked",
                    summary="Report truth or action flag rejected",
                    safe_ids=(report.report_id,),
                )
            )
        if report.knowledge_promoted:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_knowledge_promotion_blocked",
                    summary="Report knowledge promotion rejected",
                    safe_ids=(report.report_id,),
                )
            )
        if report.belief_mutated:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_belief_mutation_blocked",
                    summary="Report belief mutation rejected",
                    safe_ids=(report.report_id,),
                )
            )
    return _report("integrity-expert-reports", findings, clock=clock)


def audit_critiques(
    critiques: tuple[ExpertCritique, ...],
    reports: tuple[ExpertPerspectiveReport, ...],
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit critique references and self-review rejection."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    report_ids = {report.report_id for report in reports}
    critique_ids = [critique.critique_id for critique in critiques]
    if len(set(critique_ids)) != len(critique_ids):
        findings.append(
            _finding(
                index=1,
                reason_code="domain_mesh_circular_critique_rejected",
                summary="Duplicate critique identifier rejected",
            )
        )
    for critique in critiques:
        if critique.critic_profile_id == critique.target_profile_id:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_self_review_rejected",
                    summary="Critique self-review rejected",
                    safe_ids=(critique.critique_id,),
                )
            )
        if critique.target_report_id not in report_ids:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_evidence_reference_unresolved",
                    summary="Critique target report unresolved",
                    safe_ids=(critique.critique_id,),
                )
            )
    return _report("integrity-expert-critiques", findings, clock=clock)


def audit_disagreement_matrix(
    matrix: ExpertDisagreementMatrix,
    reports: tuple[ExpertPerspectiveReport, ...],
    critiques: tuple[ExpertCritique, ...],
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit disagreement references and dissent preservation."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    report_ids = {report.report_id for report in reports}
    critique_ids = {critique.critique_id for critique in critiques}
    if set(matrix.preserved_report_ids) != report_ids:
        findings.append(
            _finding(
                index=1,
                reason_code="domain_mesh_dissent_preserved",
                summary="Disagreement matrix did not preserve all reports",
            )
        )
    if set(matrix.preserved_critique_ids) != critique_ids:
        findings.append(
            _finding(
                index=len(findings) + 1,
                reason_code="domain_mesh_dissent_preserved",
                summary="Disagreement matrix did not preserve all critiques",
            )
        )
    return _report(f"integrity-{matrix.matrix_id}", findings, clock=clock)


def audit_mesh_synthesis(
    synthesis: ExpertMeshSynthesis,
    case: object | None = None,
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit synthesis confidence and high-stakes abstention."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    if synthesis.synthesis_confidence_cap > synthesis.underlying_assessment_confidence_cap:
        findings.append(
            _finding(
                index=1,
                reason_code="domain_mesh_confidence_non_amplification_enforced",
                summary="Synthesis confidence exceeds underlying cap",
            )
        )
    if synthesis.synthesis_confidence_cap > synthesis.report_confidence_cap:
        findings.append(
            _finding(
                index=len(findings) + 1,
                reason_code="domain_mesh_confidence_non_amplification_enforced",
                summary="Synthesis confidence exceeds report cap",
            )
        )
    if getattr(case, "risk_class", None) in {CaseRiskClass.HIGH, CaseRiskClass.CRITICAL}:
        if not synthesis.explicit_abstention or not synthesis.operator_review_required:
            findings.append(
                _finding(
                    index=len(findings) + 1,
                    reason_code="domain_mesh_high_stakes_abstention",
                    summary="High-stakes synthesis abstention missing",
                )
            )
    if (
        synthesis.truth_decision
        or synthesis.claim_accepted
        or synthesis.claim_rejected
        or synthesis.automatic_action
    ):
        findings.append(
            _finding(
                index=len(findings) + 1,
                reason_code="domain_mesh_automatic_action_blocked",
                summary="Synthesis truth or action flag rejected",
            )
        )
    return _report(f"integrity-{synthesis.synthesis_id}", findings, clock=clock)


def audit_domain_expert_mesh_session(
    session: DomainExpertMeshSession,
    *,
    clock: object = utc_now,
) -> DomainExpertMeshIntegrityReport:
    """Audit the complete immutable in-memory session."""

    findings: list[DomainExpertMeshIntegrityFinding] = []
    reports = (
        audit_panel_plan(session.panel_plan, clock=clock),
        audit_expert_reports(session.reports, clock=clock),
        audit_critiques(session.critiques, session.reports, clock=clock),
        audit_disagreement_matrix(
            session.disagreement_matrix, session.reports, session.critiques, clock=clock
        ),
        audit_mesh_synthesis(session.synthesis, session.case, clock=clock),
    )
    for report in reports:
        findings.extend(report.findings)
    if (
        session.persistent_write_applied
        or session.model_provider_called
        or session.tool_executed
        or session.network_accessed
        or session.automatic_action
        or session.knowledge_promoted
        or session.belief_mutated
        or session.runtime_effect
    ):
        findings.append(
            _finding(
                index=len(findings) + 1,
                reason_code="domain_mesh_runtime_disabled",
                summary="Session runtime or persistence effect rejected",
            )
        )
    return _report(f"integrity-{session.session_id}", findings, clock=clock)


__all__ = [
    "audit_critiques",
    "audit_disagreement_matrix",
    "audit_domain_expert_mesh_session",
    "audit_domain_taxonomy",
    "audit_expert_profile_registry",
    "audit_expert_reports",
    "audit_mesh_synthesis",
    "audit_panel_plan",
]
