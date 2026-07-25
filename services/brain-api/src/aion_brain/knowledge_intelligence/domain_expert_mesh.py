"""Controlled deterministic domain expert mesh service."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    DomainExpertCase,
    DomainExpertMeshError,
    DomainExpertMeshFixtureEnvelope,
    DomainExpertMeshIntegrityFinding,
    DomainExpertMeshIntegrityReport,
    DomainExpertMeshQuery,
    DomainExpertMeshQueryResult,
    DomainExpertMeshResourceUsage,
    DomainExpertMeshSession,
    ExpertCritique,
    ExpertCritiqueResponse,
    ExpertDisagreementMatrix,
    ExpertMeshSynthesis,
    ExpertPanelPlan,
    ExpertPerspectiveReport,
    ExpertPerspectiveRole,
    ExpertSubquestion,
    ExpertSubquestionPlan,
    MeshIntegrityStatus,
    MeshSessionOutcome,
    assert_fixture_path_allowed,
    domain_expert_mesh_fixture_fingerprint,
    domain_expert_mesh_integrity_report_fingerprint,
    domain_expert_mesh_query_result_fingerprint,
    domain_expert_mesh_session_fingerprint,
    domain_mesh_fingerprint,
    evaluate_domain_expert_mesh_budget,
    expert_subquestion_fingerprint,
    expert_subquestion_plan_fingerprint,
)
from aion_brain.contracts.knowledge_epistemic_assessment import ClaimEpistemicAssessment
from aion_brain.contracts.knowledge_research import utc_now
from aion_brain.knowledge_intelligence.domain_expert_deliberation import (
    build_disagreement_matrix,
    generate_expert_critique_responses,
    generate_expert_critiques,
    generate_expert_reports,
)
from aion_brain.knowledge_intelligence.domain_expert_evidence import (
    build_mesh_diagnostics,
    build_mesh_evidence_bundle,
    build_operator_review_item,
)
from aion_brain.knowledge_intelligence.domain_expert_integrity import (
    audit_critiques,
    audit_disagreement_matrix,
    audit_domain_expert_mesh_session,
    audit_domain_taxonomy,
    audit_expert_profile_registry,
    audit_expert_reports,
    audit_mesh_synthesis,
    audit_panel_plan,
)
from aion_brain.knowledge_intelligence.domain_expert_profiles import (
    build_default_domain_taxonomy,
    build_default_profile_registry,
)
from aion_brain.knowledge_intelligence.domain_expert_routing import (
    required_panel_roles,
    select_expert_panel,
)

SUBQUESTION_CATEGORIES: tuple[tuple[str, ExpertPerspectiveRole], ...] = (
    ("domain-interpretation", ExpertPerspectiveRole.DOMAIN_ANALYST),
    ("evidence-sufficiency", ExpertPerspectiveRole.EVIDENCE_AUDITOR),
    ("source-independence", ExpertPerspectiveRole.EVIDENCE_AUDITOR),
    ("methodological-assumptions", ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC),
    ("limitations", ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC),
    ("valid-time-applicability", ExpertPerspectiveRole.TEMPORAL_SCOPE_REVIEWER),
    ("jurisdiction-applicability", ExpertPerspectiveRole.JURISDICTION_REVIEWER),
    ("version-applicability", ExpertPerspectiveRole.VERSION_REVIEWER),
    ("unresolved-contradiction", ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC),
    ("risk-and-consequence", ExpertPerspectiveRole.RISK_REVIEWER),
    ("cross-domain-conflict", ExpertPerspectiveRole.CROSS_DOMAIN_REVIEWER),
    ("synthesis-constraints", ExpertPerspectiveRole.SYNTHESIS_COORDINATOR),
)

DECOMPOSITION_POLICY_FINGERPRINT = domain_mesh_fingerprint(
    {
        "policy": "aion-domain-expert-case-decomposition-v1",
        "inputs": (
            "explicit domains",
            "explicit specialties",
            "explicit claims",
            "explicit assessments",
            "explicit scope",
            "explicit risk",
            "required perspective roles",
        ),
        "model_inference_used": False,
        "external_research_requested": False,
    },
    "decomposition_policy_fingerprint",
)


def _now(clock: object) -> datetime:
    value = clock() if callable(clock) else utc_now()
    return value if isinstance(value, datetime) else utc_now()


def _assessment_index(
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> dict[str, ClaimEpistemicAssessment]:
    return {assessment.assessment_id: assessment for assessment in assessments}


def _resolve_assessments(
    case: DomainExpertCase,
    assessments: Iterable[ClaimEpistemicAssessment],
) -> tuple[ClaimEpistemicAssessment, ...]:
    ordered = tuple(sorted(assessments, key=lambda item: item.assessment_id))
    by_id = _assessment_index(ordered)
    missing = [item for item in case.epistemic_assessment_ids if item not in by_id]
    if missing:
        raise DomainExpertMeshError("domain expert mesh assessment reference unresolved")
    for claim_id in case.claim_ids:
        if not any(item.claim_id == claim_id for item in by_id.values()):
            raise DomainExpertMeshError("domain expert mesh claim reference unresolved")
    return tuple(by_id[item] for item in case.epistemic_assessment_ids)


def decompose_domain_expert_case(case: DomainExpertCase) -> ExpertSubquestionPlan:
    """Deterministically decompose a case from explicit metadata only."""

    required_roles = set(required_panel_roles(case))
    subquestions: list[ExpertSubquestion] = []
    for category, role in SUBQUESTION_CATEGORIES:
        if role not in required_roles and role not in {
            ExpertPerspectiveRole.EVIDENCE_AUDITOR,
            ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC,
            ExpertPerspectiveRole.SYNTHESIS_COORDINATOR,
        }:
            continue
        payload = {
            "subquestion_id": f"subquestion-{case.case_id}-{category}",
            "case_id": case.case_id,
            "category": category,
            "perspective_role": role,
            "domain_ids": case.domain_ids,
            "specialty_ids": case.specialty_ids,
            "claim_ids": case.claim_ids,
            "assessment_ids": case.epistemic_assessment_ids,
        }
        subquestions.append(
            ExpertSubquestion.model_validate(
                {**payload, "subquestion_fingerprint": expert_subquestion_fingerprint(payload)}
            )
        )
    for index, _ in enumerate(case.explicit_subquestions, start=1):
        payload = {
            "subquestion_id": f"subquestion-{case.case_id}-operator-explicit-{index:02d}",
            "case_id": case.case_id,
            "category": "operator-explicit",
            "perspective_role": ExpertPerspectiveRole.DOMAIN_ANALYST,
            "domain_ids": case.domain_ids,
            "specialty_ids": case.specialty_ids,
            "claim_ids": case.claim_ids,
            "assessment_ids": case.epistemic_assessment_ids,
        }
        subquestions.append(
            ExpertSubquestion.model_validate(
                {**payload, "subquestion_fingerprint": expert_subquestion_fingerprint(payload)}
            )
        )
    bounded = tuple(sorted(subquestions, key=lambda item: item.subquestion_id))[:50]
    plan_payload: dict[str, object] = {
        "plan_id": f"subquestion-plan-{case.case_id}",
        "case_id": case.case_id,
        "subquestions": bounded,
        "subquestion_count": len(bounded),
        "decomposition_policy_fingerprint": DECOMPOSITION_POLICY_FINGERPRINT,
    }
    return ExpertSubquestionPlan.model_validate(
        {
            **plan_payload,
            "plan_fingerprint": expert_subquestion_plan_fingerprint(plan_payload),
        }
    )


class InMemoryDomainExpertMeshRepository:
    """Per-instance in-memory repository with no persistence backend."""

    def __init__(self, sessions: Iterable[DomainExpertMeshSession] = ()) -> None:
        self._sessions = {session.session_id: session for session in sessions}

    def add(self, session: DomainExpertMeshSession) -> None:
        """Store one immutable session in this in-memory instance."""

        self._sessions[session.session_id] = session

    def snapshot(self) -> tuple[DomainExpertMeshSession, ...]:
        """Return deterministic immutable session snapshot."""

        return tuple(self._sessions[key] for key in sorted(self._sessions))

    def reject_persistent_write(self, payload: object | None = None) -> MeshSessionOutcome:
        """Reject any request to write mesh state persistently."""

        _ = payload
        return MeshSessionOutcome.PERSISTENT_WRITE_DISABLED


def _aggregate_integrity(
    reports: tuple[DomainExpertMeshIntegrityReport, ...],
    *,
    clock: object,
) -> DomainExpertMeshIntegrityReport:
    findings: list[DomainExpertMeshIntegrityFinding] = []
    for report in reports:
        findings.extend(report.findings)
    now = _now(clock)
    status = MeshIntegrityStatus.FAILED if findings else MeshIntegrityStatus.PASSED
    reason_codes = (
        ("domain_mesh_integrity_failed",) if findings else ("domain_mesh_integrity_passed",)
    )
    payload = {
        "report_id": "integrity-domain-expert-mesh-session-artifacts",
        "status": status,
        "finding_count": len(findings),
        "findings": tuple(findings),
        "reason_codes": reason_codes,
        "audit_timestamp": now,
    }
    return DomainExpertMeshIntegrityReport.model_validate(
        {**payload, "report_fingerprint": domain_expert_mesh_integrity_report_fingerprint(payload)}
    )


class ExplicitLocalDomainExpertMeshFixtureReplay:
    """Read one explicit local synthetic fixture outside the repository."""

    def __init__(self, *, repository_root: Path, clock: object = utc_now) -> None:
        self.repository_root = repository_root
        self.clock = clock

    def load_fixture(self, path: Path) -> DomainExpertMeshFixtureEnvelope:
        """Load and validate a fixture envelope."""

        fixture_path = assert_fixture_path_allowed(path, repository_root=self.repository_root)
        try:
            payload_text = fixture_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise DomainExpertMeshError("fixture must be valid UTF-8") from exc
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise DomainExpertMeshError("fixture JSON rejected") from exc
        if not isinstance(payload, dict):
            raise DomainExpertMeshError("fixture envelope must be an object")
        if len(payload_text.encode("utf-8")) > 4_194_304:
            raise DomainExpertMeshError("fixture byte limit exceeded")
        return DomainExpertMeshFixtureEnvelope.model_validate(payload)


class ControlledDomainExpertMesh:
    """Pure in-memory deterministic domain expert mesh."""

    def __init__(
        self,
        *,
        repository: InMemoryDomainExpertMeshRepository | None = None,
        clock: object = utc_now,
        repository_root: Path | None = None,
    ) -> None:
        self.repository = repository or InMemoryDomainExpertMeshRepository()
        self.clock = clock
        self.repository_root = repository_root or Path.cwd()

    def plan_case(self, case: DomainExpertCase) -> ExpertSubquestionPlan:
        """Build a deterministic decomposition plan."""

        return decompose_domain_expert_case(case)

    def route_panel(self, case: DomainExpertCase) -> ExpertPanelPlan:
        """Build a deterministic panel plan."""

        taxonomy = build_default_domain_taxonomy()
        registry = build_default_profile_registry(taxonomy)
        return select_expert_panel(case, registry, taxonomy=taxonomy)

    def generate_reports(
        self,
        case: DomainExpertCase,
        panel_plan: ExpertPanelPlan,
        assessments: tuple[ClaimEpistemicAssessment, ...],
    ) -> tuple[ExpertPerspectiveReport, ...]:
        """Generate expert reports."""

        return generate_expert_reports(case, panel_plan, assessments)

    def generate_critiques(
        self,
        reports: tuple[ExpertPerspectiveReport, ...],
    ) -> tuple[ExpertCritique, ...]:
        """Generate cross-examination critiques."""

        return generate_expert_critiques(reports)

    def generate_critique_responses(
        self,
        critiques: tuple[ExpertCritique, ...],
    ) -> tuple[ExpertCritiqueResponse, ...]:
        """Generate critique responses."""

        return generate_expert_critique_responses(critiques)

    def build_disagreement_matrix(
        self,
        case: DomainExpertCase,
        panel_plan: ExpertPanelPlan,
        reports: tuple[ExpertPerspectiveReport, ...],
        critiques: tuple[ExpertCritique, ...],
    ) -> ExpertDisagreementMatrix:
        """Build disagreement matrix."""

        return build_disagreement_matrix(case, panel_plan, reports, critiques)

    def synthesize(
        self,
        case: DomainExpertCase,
        panel_plan: ExpertPanelPlan,
        reports: tuple[ExpertPerspectiveReport, ...],
        critiques: tuple[ExpertCritique, ...],
        matrix: ExpertDisagreementMatrix,
    ) -> ExpertMeshSynthesis:
        """Build advisory synthesis."""

        from aion_brain.knowledge_intelligence.domain_expert_synthesis import (
            synthesize_expert_mesh,
        )

        return synthesize_expert_mesh(case, panel_plan, reports, critiques, matrix)

    def audit(self, session: DomainExpertMeshSession) -> DomainExpertMeshIntegrityReport:
        """Audit a complete session."""

        return audit_domain_expert_mesh_session(session, clock=self.clock)

    def reject_persistent_write(self, payload: object | None = None) -> MeshSessionOutcome:
        """Reject persistent writes because the authorized batch size is zero."""

        return self.repository.reject_persistent_write(payload)

    def run_session(
        self,
        *,
        case: DomainExpertCase,
        assessments: Iterable[ClaimEpistemicAssessment],
    ) -> DomainExpertMeshSession:
        """Run a deterministic in-memory session."""

        taxonomy = build_default_domain_taxonomy()
        registry = build_default_profile_registry(taxonomy)
        resolved_assessments = _resolve_assessments(case, assessments)
        subquestion_plan = self.plan_case(case)
        panel_plan = select_expert_panel(case, registry, taxonomy=taxonomy)
        usage = DomainExpertMeshResourceUsage(
            domains_per_case=len(case.domain_ids),
            specialties_per_case=len(case.specialty_ids),
            claims_per_case=len(case.claim_ids),
            epistemic_assessments_per_case=len(case.epistemic_assessment_ids),
            subquestions_per_case=subquestion_plan.subquestion_count,
            expert_profiles_considered=len(registry.profiles),
            panel_size=panel_plan.panel_size,
            required_roles_per_panel=len(panel_plan.required_roles),
            mesh_sessions=1,
            concurrent_experts=min(panel_plan.panel_size, 8),
        )
        budget_decision = evaluate_domain_expert_mesh_budget(usage)
        if not budget_decision.within_budget:
            raise DomainExpertMeshError("domain expert mesh budget exceeded")
        reports = generate_expert_reports(case, panel_plan, resolved_assessments)
        critiques = generate_expert_critiques(reports)
        critique_responses = generate_expert_critique_responses(critiques)
        matrix = build_disagreement_matrix(case, panel_plan, reports, critiques)
        synthesis = self.synthesize(case, panel_plan, reports, critiques, matrix)
        integrity_report = _aggregate_integrity(
            (
                audit_domain_taxonomy(taxonomy, clock=self.clock),
                audit_expert_profile_registry(registry, clock=self.clock),
                audit_panel_plan(panel_plan, clock=self.clock),
                audit_expert_reports(reports, clock=self.clock),
                audit_critiques(critiques, reports, clock=self.clock),
                audit_disagreement_matrix(matrix, reports, critiques, clock=self.clock),
                audit_mesh_synthesis(synthesis, case, clock=self.clock),
            ),
            clock=self.clock,
        )
        session_id = f"session-{case.case_id}"
        diagnostics = build_mesh_diagnostics(
            session_id=session_id,
            case_risk_class=case.risk_class,
            panel_plan=panel_plan,
            reports=reports,
            matrix=matrix,
            synthesis=synthesis,
            integrity_report=integrity_report,
        )
        review_items = (
            (
                build_operator_review_item(
                    session_id=session_id,
                    case_id=case.case_id,
                    reason_codes=tuple(
                        dict.fromkeys(
                            synthesis.synthesis_codes + ("domain_mesh_operator_review_required",)
                        )
                    ),
                    clock=self.clock,
                ),
            )
            if synthesis.operator_review_required
            else ()
        )
        evidence_bundle = build_mesh_evidence_bundle(
            session_id=session_id,
            case_id=case.case_id,
            domain_ids=case.domain_ids,
            specialty_ids=case.specialty_ids,
            risk_class=case.risk_class,
            panel_plan=panel_plan,
            reports=reports,
            matrix=matrix,
            synthesis=synthesis,
            integrity_report=integrity_report,
        )
        outcome = (
            MeshSessionOutcome.INTEGRITY_BLOCKED
            if integrity_report.status == MeshIntegrityStatus.FAILED
            else MeshSessionOutcome.COMPLETED_WITH_ABSTENTION
            if synthesis.explicit_abstention
            else MeshSessionOutcome.COMPLETED
        )
        payload = {
            "session_id": session_id,
            "case": case,
            "subquestion_plan": subquestion_plan,
            "panel_plan": panel_plan,
            "reports": reports,
            "critiques": critiques,
            "critique_responses": critique_responses,
            "disagreement_matrix": matrix,
            "synthesis": synthesis,
            "integrity_report": integrity_report,
            "diagnostics": diagnostics,
            "operator_review_items": review_items,
            "evidence_bundle": evidence_bundle,
            "outcome": outcome,
            "created_at": _now(self.clock),
        }
        session = DomainExpertMeshSession.model_validate(
            {**payload, "session_fingerprint": domain_expert_mesh_session_fingerprint(payload)}
        )
        self.repository.add(session)
        return session

    def replay_fixture(self, path: Path) -> DomainExpertMeshSession:
        """Replay a synthetic explicit local fixture."""

        replay = ExplicitLocalDomainExpertMeshFixtureReplay(
            repository_root=self.repository_root,
            clock=self.clock,
        )
        fixture = replay.load_fixture(path)
        return self.run_session(case=fixture.case, assessments=fixture.assessments)

    def query(self, query: DomainExpertMeshQuery) -> DomainExpertMeshQueryResult:
        """Run a bounded exact query over in-memory sessions."""

        matches: list[DomainExpertMeshSession] = []
        for session in self.repository.snapshot():
            if _matches_query(session, query):
                matches.append(session)
        limited = tuple(item.session_id for item in matches[: query.limit])
        payload = {
            "query": query,
            "session_ids": limited,
            "result_count": len(limited),
            "truncated": len(matches) > query.limit,
        }
        return DomainExpertMeshQueryResult.model_validate(
            {**payload, "query_fingerprint": domain_expert_mesh_query_result_fingerprint(payload)}
        )


def _matches_query(session: DomainExpertMeshSession, query: DomainExpertMeshQuery) -> bool:
    if query.session_id is not None and session.session_id != query.session_id:
        return False
    if query.case_id is not None and session.case.case_id != query.case_id:
        return False
    if query.panel_id is not None and session.panel_plan.panel_id != query.panel_id:
        return False
    if query.profile_id is not None and not any(
        assignment.profile_id == query.profile_id for assignment in session.panel_plan.assignments
    ):
        return False
    if query.perspective_role is not None and not any(
        report.perspective_role == query.perspective_role for report in session.reports
    ):
        return False
    if query.domain_id is not None and query.domain_id not in session.case.domain_ids:
        return False
    if query.specialty_id is not None and query.specialty_id not in session.case.specialty_ids:
        return False
    if query.risk_class is not None and session.case.risk_class != query.risk_class:
        return False
    if query.report_position is not None and not any(
        report.position == query.report_position for report in session.reports
    ):
        return False
    if query.disagreement_type is not None and not any(
        item.disagreement_type == query.disagreement_type
        for item in session.disagreement_matrix.disagreements
    ):
        return False
    if (
        query.alignment_state is not None
        and session.synthesis.alignment_state != query.alignment_state
    ):
        return False
    if (
        query.explicit_abstention is not None
        and session.synthesis.explicit_abstention != query.explicit_abstention
    ):
        return False
    if (
        query.operator_review_required is not None
        and session.synthesis.operator_review_required != query.operator_review_required
    ):
        return False
    return True


def domain_expert_mesh_fixture_payload(
    *,
    case: DomainExpertCase,
    assessments: tuple[ClaimEpistemicAssessment, ...],
) -> dict[str, Any]:
    """Return a fixture payload with deterministic fingerprint."""

    payload = {"case": case, "assessments": assessments}
    return {**payload, "fixture_fingerprint": domain_expert_mesh_fixture_fingerprint(payload)}


__all__ = [
    "ControlledDomainExpertMesh",
    "DECOMPOSITION_POLICY_FINGERPRINT",
    "ExplicitLocalDomainExpertMeshFixtureReplay",
    "InMemoryDomainExpertMeshRepository",
    "SUBQUESTION_CATEGORIES",
    "decompose_domain_expert_case",
    "domain_expert_mesh_fixture_payload",
]
