"""Release candidate report service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.release_candidate import RCGateRun, RCReport
from aion_brain.release_candidate.policy import authorize_rc_action
from aion_brain.release_candidate.redaction import safe_rc_summary
from aion_brain.release_candidate.repository import ReleaseCandidateRepository
from aion_brain.release_candidate.telemetry import emit_rc_telemetry

_RECOMMENDATION_ORDER = [
    "fix_failed_required_check",
    "rerun_scripts_check",
    "rerun_golden_path",
    "rerun_bootstrap_doctor",
    "rerun_freeze_gate",
    "inspect_contract_drift",
    "inspect_registry_integrity",
    "inspect_operator_overview",
    "create_release_package_after_green",
    "tag_release_candidate",
]


class RCReportService:
    """Create and query release candidate reports."""

    def __init__(
        self,
        repository: ReleaseCandidateRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_report(self, run: RCGateRun, created_by: str | None = None) -> RCReport:
        """Create a local RC report from a completed gate run."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.report.create",
            run.owner_scope,
            actor_id=created_by,
            trace_id=run.trace_id,
            resource_type="rc_report",
            risk_level="medium",
            context={"source_mutation": False, "external_calls": False},
        )
        passed = [check.check_key for check in run.verification_checks if check.status == "passed"]
        failed = [
            check.check_key
            for check in run.verification_checks
            if check.status in {"failed", "blocked", "unknown"}
        ]
        warnings = [
            check.check_key for check in run.verification_checks if check.status == "warning"
        ]
        recommendations = _recommendations(run, failed, warnings)
        report_payload = safe_rc_summary(
            {
                "rc_run_id": run.rc_run_id,
                "release_candidate_id": run.release_candidate_id,
                "readiness_score": run.readiness_score,
                "release_ready": run.release_ready,
                "checks_total": run.checks_total,
                "blocker_count": run.blocker_count,
                "warnings": run.warnings,
                "failures": run.failures,
                "no_external_calls": True,
                "no_deployment": True,
                "no_source_mutation": True,
            }
        )
        report = RCReport(
            rc_report_id=f"rc-report-{uuid4().hex}",
            trace_id=run.trace_id,
            release_candidate_id=run.release_candidate_id,
            rc_run_id=run.rc_run_id,
            status=run.status,
            owner_scope=run.owner_scope,
            version=str(run.result.get("version", "0.1.0")),
            readiness_score=run.readiness_score,
            release_ready=run.release_ready,
            blocker_count=run.blocker_count,
            warning_count=run.checks_warning,
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            findings=[finding.model_dump(mode="json") for finding in run.findings],
            recommendations=recommendations,
            report=report_payload,
            metadata={"external_calls": False, "deployment": False, "source_mutation": False},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_report(report)
        emit_rc_telemetry(
            self._telemetry_service,
            event_type="rc_report_created",
            node_type="rc_report",
            node_id=saved.rc_report_id,
            scope=saved.owner_scope,
            intensity=saved.readiness_score,
            payload={"status": saved.status, "release_ready": saved.release_ready},
        )
        return saved

    def get_report(self, rc_report_id: str, scope: list[str]) -> RCReport | None:
        """Return one report."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.report.read",
            scope,
            resource_type="rc_report",
            resource_id=rc_report_id,
        )
        return self._repository.get_report(rc_report_id)

    def list_reports(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        version: str | None = None,
        limit: int = 50,
    ) -> list[RCReport]:
        """List reports."""

        authorize_rc_action(self._policy_adapter, "release_candidate.report.read", scope)
        return self._repository.list_reports(status=status, version=version, limit=limit)


def _recommendations(run: RCGateRun, failed: list[str], warnings: list[str]) -> list[str]:
    selected: set[str] = set()
    if failed:
        selected.add("fix_failed_required_check")
    if any(item in failed for item in {"tests.brain", "tests.sdk", "lint", "typecheck"}):
        selected.add("rerun_scripts_check")
    if "golden_path" in failed:
        selected.add("rerun_golden_path")
    if "bootstrap_doctor" in failed or "bootstrap_doctor" in warnings:
        selected.add("rerun_bootstrap_doctor")
    if "freeze_gate" in failed:
        selected.add("rerun_freeze_gate")
    if "contract_registry" in failed:
        selected.add("inspect_contract_drift")
    if "resource_registry" in failed:
        selected.add("inspect_registry_integrity")
    if "operator_overview" in failed or "operator_overview" in warnings:
        selected.add("inspect_operator_overview")
    if run.release_ready:
        selected.add("create_release_package_after_green")
        selected.add("tag_release_candidate")
    return [item for item in _RECOMMENDATION_ORDER if item in selected]


__all__ = ["RCReportService"]
