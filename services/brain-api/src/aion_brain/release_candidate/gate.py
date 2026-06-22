"""Release candidate gate aggregator and scorer."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.release_candidate import (
    RCFinding,
    RCGateRun,
    RCGateRunRequest,
    RCGateRunStatus,
    ReleaseCandidateCreateRequest,
)
from aion_brain.contracts.verification_matrix import VerificationCheck, VerificationMatrix
from aion_brain.release_candidate.candidates import ReleaseCandidateService
from aion_brain.release_candidate.checks import VerificationCheckCollector
from aion_brain.release_candidate.evidence_pack import RCEvidencePackService
from aion_brain.release_candidate.findings import RCFindingService
from aion_brain.release_candidate.matrix import VerificationMatrixService
from aion_brain.release_candidate.policy import authorize_rc_action
from aion_brain.release_candidate.redaction import safe_rc_summary
from aion_brain.release_candidate.reports import RCReportService
from aion_brain.release_candidate.repository import ReleaseCandidateRepository
from aion_brain.release_candidate.telemetry import emit_rc_telemetry


class RCGateService:
    """Run the deterministic release candidate gate."""

    def __init__(
        self,
        repository: ReleaseCandidateRepository,
        policy_adapter: object,
        *,
        candidate_service: ReleaseCandidateService,
        matrix_service: VerificationMatrixService,
        check_collector: VerificationCheckCollector,
        finding_service: RCFindingService,
        evidence_pack_service: RCEvidencePackService,
        report_service: RCReportService,
        autonomy_governor: object | None = None,
        notification_router: object | None = None,
        operator_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._candidate_service = candidate_service
        self._matrix_service = matrix_service
        self._check_collector = check_collector
        self._finding_service = finding_service
        self._evidence_pack_service = evidence_pack_service
        self._report_service = report_service
        self._autonomy_governor = autonomy_governor
        self._notification_router = notification_router
        self._operator_repository = operator_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings or get_settings()

    def run(self, request: RCGateRunRequest) -> RCGateRun:
        """Run the local RC gate and persist RC-owned evidence."""

        if not self._settings.rc_gate_enabled:
            return self._blocked_run(request, "rc_gate_disabled")
        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.gate.run",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="rc_gate_run",
            resource_id=request.rc_run_id,
            risk_level="medium",
            context=_run_context(request),
        )
        if request.mode == "controlled" and not self._settings.rc_controlled_mode_enabled:
            return self._blocked_run(request, "controlled_rc_gate_disabled")

        rc_run_id = request.rc_run_id or f"rc-run-{uuid4().hex}"
        trace_id = request.trace_id or f"trace-rc-{uuid4().hex}"
        started_at = datetime.now(UTC)
        version = request.version or self._settings.version
        self._emit(
            "rc_gate_started",
            "rc_gate",
            rc_run_id,
            request.owner_scope,
            0.5,
            {"mode": request.mode, "version": version},
        )

        candidate_id = self._resolve_candidate(request, trace_id, version)
        matrix = self._resolve_matrix(request, version)
        checks = self._collect_checks(request, rc_run_id, trace_id, matrix)
        checks = [self._repository.save_check(check) for check in checks]

        findings = []
        for check in checks:
            if _needs_finding(check):
                findings.append(
                    self._finding_service.create_for_check(
                        check,
                        trace_id=trace_id,
                        rc_run_id=rc_run_id,
                        release_candidate_id=candidate_id,
                    )
                )

        score = _readiness_score(checks, matrix)
        blockers = [finding for finding in findings if finding.blocking]
        critical_findings = [finding for finding in findings if finding.severity == "critical"]
        release_ready = (
            score >= matrix.release_ready_threshold
            and not blockers
            and not (matrix.fail_on_critical and critical_findings)
        )
        status = _run_status(request.mode, release_ready, blockers, checks)
        failures = [
            {"check_key": check.check_key, "status": check.status, "severity": check.severity}
            for check in checks
            if check.status in {"failed", "blocked", "unknown"}
        ]
        warnings = [
            {"check_key": check.check_key, "status": check.status, "severity": check.severity}
            for check in checks
            if check.status == "warning"
        ]
        run = RCGateRun(
            rc_run_id=rc_run_id,
            trace_id=trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            release_candidate_id=candidate_id,
            verification_matrix_id=matrix.verification_matrix_id,
            status=status,
            mode=request.mode,
            owner_scope=request.owner_scope,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            checks_total=len(checks),
            checks_passed=sum(1 for check in checks if check.status == "passed"),
            checks_failed=sum(
                1 for check in checks if check.status in {"failed", "blocked", "unknown"}
            ),
            checks_warning=sum(1 for check in checks if check.status == "warning"),
            checks_skipped=sum(1 for check in checks if check.status == "skipped"),
            blocker_count=len(blockers),
            readiness_score=score,
            release_ready=release_ready,
            verification_checks=checks,
            findings=findings,
            evidence_pack_id=None,
            warnings=warnings,
            failures=failures,
            result={
                "version": version,
                "matrix_key": matrix.matrix_key,
                "external_calls": False,
                "deployment": False,
                "publish": False,
                "source_mutation": False,
            },
            metadata=safe_rc_summary(request.metadata),
            created_by=request.created_by,
            created_at=started_at,
        )
        saved = self._repository.save_run(run)
        if self._settings.rc_evidence_pack_enabled:
            pack = self._evidence_pack_service.build(saved, created_by=request.created_by)
            saved = saved.model_copy(update={"evidence_pack_id": pack.evidence_pack_id})
            saved = self._repository.save_run(saved)
        report = self._report_service.create_report(saved, created_by=request.created_by)
        saved = saved.model_copy(
            update={"result": {**saved.result, "rc_report_id": report.rc_report_id}}
        )
        saved = self._repository.save_run(saved)
        self._record_audit(saved)
        self._emit(
            "rc_gate_completed",
            "rc_gate",
            saved.rc_run_id,
            saved.owner_scope,
            saved.readiness_score,
            {"status": saved.status, "release_ready": saved.release_ready},
        )
        return saved

    def get_run(self, rc_run_id: str, scope: list[str]) -> RCGateRun | None:
        """Return one RC gate run."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.run.read",
            scope,
            resource_type="rc_gate_run",
            resource_id=rc_run_id,
        )
        return self._repository.get_run(rc_run_id)

    def list_runs(
        self, scope: list[str], *, status: str | None = None, limit: int = 100
    ) -> list[RCGateRun]:
        """List RC gate runs."""

        authorize_rc_action(self._policy_adapter, "release_candidate.run.read", scope)
        return self._repository.list_runs(status=status, limit=limit)

    def status(self, scope: list[str] | None = None) -> dict[str, object]:
        """Return latest RC gate status for operator cards."""

        return self._repository.status(scope)

    def _resolve_candidate(
        self, request: RCGateRunRequest, trace_id: str, version: str
    ) -> str | None:
        if request.release_candidate_id:
            candidate = self._repository.get_candidate(request.release_candidate_id)
            if candidate is not None:
                return candidate.release_candidate_id
        if request.rc_key:
            existing = self._repository.get_candidate_by_key(request.rc_key)
            if existing is not None:
                return existing.release_candidate_id
            candidate = self._candidate_service.create_candidate(
                ReleaseCandidateCreateRequest(
                    trace_id=trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    rc_key=request.rc_key,
                    version=version,
                    owner_scope=request.owner_scope,
                    verification_matrix_id=request.verification_matrix_id,
                    metadata={"created_by_rc_gate": True},
                    created_by=request.created_by,
                )
            )
            return candidate.release_candidate_id
        return None

    def _resolve_matrix(self, request: RCGateRunRequest, version: str) -> VerificationMatrix:
        if request.verification_matrix_id:
            matrix = self._repository.get_matrix(request.verification_matrix_id)
            if matrix is not None:
                return matrix
        existing = self._repository.get_matrix_by_key("rc.v0_1.default", version)
        if existing is not None:
            return existing
        return self._matrix_service.default_matrix(
            request.owner_scope, created_by=request.created_by
        )

    def _collect_checks(
        self,
        request: RCGateRunRequest,
        rc_run_id: str,
        trace_id: str,
        matrix: VerificationMatrix,
    ) -> list[VerificationCheck]:
        provided = [
            check.model_copy(update={"rc_run_id": rc_run_id, "trace_id": trace_id})
            for check in request.check_results
        ]
        collected = []
        if request.run_service_checks:
            collected = [
                check.model_copy(update={"rc_run_id": rc_run_id, "trace_id": trace_id})
                for check in self._check_collector.collect_service_checks(request)
            ]
        by_key: dict[str, VerificationCheck] = {}
        for check in [*collected, *provided]:
            by_key[check.check_key] = check
        for check_key in matrix.required_checks:
            if check_key not in by_key:
                by_key[check_key] = self._check_collector.build_check(
                    check_key,
                    "unknown",
                    {"message": "missing_required_check"},
                    required=True,
                    summary="Required check was not supplied to the RC gate.",
                ).model_copy(update={"rc_run_id": rc_run_id, "trace_id": trace_id})
        for check_key in matrix.optional_checks:
            if check_key not in by_key:
                by_key[check_key] = self._check_collector.build_check(
                    check_key,
                    "skipped",
                    {"message": "optional_check_not_supplied"},
                    required=False,
                    summary="Optional check was not supplied to the RC gate.",
                ).model_copy(update={"rc_run_id": rc_run_id, "trace_id": trace_id})
        order = [*matrix.required_checks, *matrix.optional_checks]
        return [by_key[key] for key in order if key in by_key]

    def _blocked_run(self, request: RCGateRunRequest, reason: str) -> RCGateRun:
        now = datetime.now(UTC)
        return RCGateRun(
            rc_run_id=request.rc_run_id or f"rc-run-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            release_candidate_id=request.release_candidate_id,
            verification_matrix_id=request.verification_matrix_id,
            status="blocked",
            mode=request.mode,
            owner_scope=request.owner_scope,
            started_at=now,
            completed_at=now,
            checks_total=0,
            checks_passed=0,
            checks_failed=0,
            checks_warning=0,
            checks_skipped=0,
            blocker_count=1,
            readiness_score=0.0,
            release_ready=False,
            verification_checks=[],
            findings=[],
            evidence_pack_id=None,
            warnings=[],
            failures=[{"reason": reason}],
            result={"reason": reason, "external_calls": False, "source_mutation": False},
            metadata=safe_rc_summary(request.metadata),
            created_by=request.created_by,
            created_at=now,
        )

    def _record_audit(self, run: RCGateRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="release_candidate.gate.run",
            resource_type="rc_gate_run",
            resource_id=run.rc_run_id,
            event_type="rc_gate_completed",
            outcome=run.status,
            source_component="rc_gate_service",
            actor_id=run.created_by or run.actor_id,
            payload={
                "readiness_score": run.readiness_score,
                "release_ready": run.release_ready,
                "blocker_count": run.blocker_count,
            },
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        scope: list[str],
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        emit_rc_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            intensity=intensity,
            payload=payload,
        )


def _run_context(request: RCGateRunRequest) -> dict[str, object]:
    return {
        "mode": request.mode,
        "external_calls": False,
        "deployment": False,
        "publish": False,
        "source_mutation": False,
        "source_records_mutated": False,
        "enable_disabled_features": False,
        "code_loading_enabled": False,
        "full_autonomy_enabled": False,
        "controlled_records": "rc_owned_only",
    }


def _needs_finding(check: VerificationCheck) -> bool:
    if check.status in {"failed", "blocked", "unknown"}:
        return True
    return check.required and check.status == "warning"


def _readiness_score(checks: list[VerificationCheck], matrix: VerificationMatrix) -> float:
    required = [check for check in checks if check.check_key in matrix.required_checks]
    optional = [check for check in checks if check.check_key in matrix.optional_checks]
    required_score = (
        sum(1 for check in required if check.status == "passed") / len(required)
        if required
        else 0.0
    )
    optional_score = (
        sum(1 for check in optional if check.status in {"passed", "skipped"}) / len(optional)
        if optional
        else 1.0
    )
    evidence_score = 1.0 if checks and all(check.evidence for check in checks) else 0.0
    score = (required_score * 0.8) + (optional_score * 0.1) + (evidence_score * 0.1)
    return max(0.0, min(1.0, round(score, 4)))


def _run_status(
    mode: str,
    release_ready: bool,
    blockers: Sequence[RCFinding],
    checks: list[VerificationCheck],
) -> RCGateRunStatus:
    if blockers:
        return "blocked"
    if any(check.status in {"failed", "blocked", "unknown"} for check in checks if check.required):
        return "failed"
    if any(check.status == "warning" for check in checks):
        return "warning"
    if mode == "dry_run" and not release_ready:
        return "dry_run"
    return "passed" if release_ready else "failed"


__all__ = ["RCGateService"]
