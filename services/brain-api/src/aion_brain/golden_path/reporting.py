"""Golden path report builder."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.golden_path import GoldenPathReport, GoldenPathRun
from aion_brain.golden_path.policy import authorize_golden_path_action
from aion_brain.golden_path.repository import GoldenPathRepository
from aion_brain.golden_path.telemetry import emit_golden_path_telemetry


class GoldenPathReportService:
    """Create and query release-facing golden path reports."""

    def __init__(
        self,
        repository: GoldenPathRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_report(self, run: GoldenPathRun) -> GoldenPathReport:
        """Create and persist a report for a run."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.report.create",
            run.owner_scope,
            actor_id=run.created_by or run.actor_id,
            workspace_id=run.workspace_id,
            trace_id=run.trace_id,
            resource_type="golden_path_report",
            risk_level="low",
            context={"run_status": run.status, "external_calls": False},
        )
        total = len(run.assertion_results)
        passed = len([item for item in run.assertion_results if item.status == "passed"])
        failed = [item for item in run.assertion_results if item.status == "failed"]
        critical_failed = [item for item in failed if item.severity == "critical"]
        readiness_score = (passed / total) if total else 0.0
        release_ready = (
            readiness_score >= self._settings.golden_path_release_ready_threshold
            and not critical_failed
            and run.failed_count == 0
            and run.blocked_count == 0
        )
        status = (
            "failed"
            if critical_failed or run.failed_count or run.blocked_count
            else "warning"
            if run.warning_count
            else "passed"
        )
        findings = [
            {
                "assertion_result_id": item.assertion_result_id,
                "assertion_key": item.assertion_key,
                "severity": item.severity,
                "status": item.status,
                "message": item.message,
            }
            for item in failed
        ]
        report = GoldenPathReport(
            golden_path_report_id=f"golden-path-report-{uuid4().hex}",
            trace_id=run.trace_id,
            status=status,  # type: ignore[arg-type]
            owner_scope=run.owner_scope,
            golden_path_run_id=run.golden_path_run_id,
            scenario_count=len(run.scenarios),
            passed_count=run.passed_count,
            failed_count=run.failed_count,
            warning_count=run.warning_count,
            blocked_count=run.blocked_count,
            readiness_score=readiness_score,
            release_candidate_ready=release_ready,
            findings=findings,
            recommendations=_recommendations(run, failed),
            report={
                "deterministic": True,
                "dry_run": run.mode == "dry_run",
                "external_calls": False,
                "tool_execution": False,
                "source_records_mutated": False,
            },
            metadata={"threshold": self._settings.golden_path_release_ready_threshold},
            created_by=run.created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_report(report)
        emit_golden_path_telemetry(
            self._telemetry_service,
            event_type="golden_path_report_created",
            node_type="golden_path_report",
            node_id=saved.golden_path_report_id,
            scope=saved.owner_scope,
            intensity=saved.readiness_score,
            payload={
                "status": saved.status,
                "release_candidate_ready": saved.release_candidate_ready,
            },
        )
        return saved

    def get_report(
        self,
        golden_path_report_id: str,
        scope: list[str],
    ) -> GoldenPathReport | None:
        """Return one report."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.report.read",
            scope,
            resource_type="golden_path_report",
            resource_id=golden_path_report_id,
        )
        return self._repository.get_report(golden_path_report_id)

    def list_reports(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[GoldenPathReport]:
        """List reports."""
        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.report.read",
            scope,
            resource_type="golden_path_report",
        )
        return self._repository.list_reports(status=status, limit=limit)


def _recommendations(run: GoldenPathRun, failed: Sequence[object]) -> list[str]:
    recommendations = []
    if failed:
        recommendations.append("rerun_failed_scenario")
        recommendations.append("inspect_service_wiring")
    if run.blocked_count:
        recommendations.append("run_operator_overview")
    recommendations.extend(
        ["run_registry_validation", "run_contract_scan", "run_freeze_gate", "run_release_package"]
    )
    return list(dict.fromkeys(recommendations))


__all__ = ["GoldenPathReportService"]
