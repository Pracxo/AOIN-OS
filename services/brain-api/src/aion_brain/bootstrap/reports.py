"""Setup report service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.bootstrap.policy import authorize_bootstrap_action
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.bootstrap.telemetry import emit_bootstrap_telemetry
from aion_brain.contracts.setup_doctor import SetupDoctorResult, SetupReport


class SetupReportService:
    """Create and query local setup reports."""

    def __init__(
        self,
        repository: BootstrapRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_report(
        self,
        result: SetupDoctorResult,
        bootstrap_run_id: str | None = None,
        created_by: str | None = None,
        trace_id: str | None = None,
    ) -> SetupReport:
        """Create a setup report from doctor output."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.report.create",
            result.owner_scope,
            actor_id=created_by,
            trace_id=trace_id,
            resource_type="setup_report",
            risk_level="low",
            context={"external_calls": False, "status": result.status},
        )
        critical_count = len([item for item in result.findings if item.severity == "critical"])
        warning_count = len(
            [item for item in result.findings if item.severity in {"low", "medium"}]
        )
        report = SetupReport(
            setup_report_id=f"setup-report-{uuid4().hex}",
            trace_id=trace_id,
            status=result.status,
            owner_scope=result.owner_scope,
            bootstrap_run_id=bootstrap_run_id,
            readiness_score=result.readiness_score,
            local_ready=result.local_ready,
            health_ready=result.health_ready,
            policy_ready=result.policy_ready,
            sdk_ready=result.sdk_ready,
            cli_ready=result.cli_ready,
            golden_path_ready=result.golden_path_ready,
            release_smoke_ready=result.release_smoke_ready,
            docker_ready=result.docker_ready,
            finding_count=len(result.findings),
            critical_count=critical_count,
            warning_count=warning_count,
            findings=[item.model_dump(mode="json") for item in result.findings],
            recommendations=result.recommendations,
            report={
                "checks_run": result.checks_run,
                "external_calls": False,
                "package_install": False,
                "production_provisioning": False,
            },
            metadata=result.metadata,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_report(report)
        emit_bootstrap_telemetry(
            self._telemetry_service,
            event_type="setup_report_created",
            node_type="setup_report",
            node_id=saved.setup_report_id,
            scope=saved.owner_scope,
            intensity=saved.readiness_score,
            payload={"status": saved.status, "local_ready": saved.local_ready},
        )
        return saved

    def get_report(self, setup_report_id: str, scope: list[str]) -> SetupReport | None:
        """Return one setup report."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.report.read",
            scope,
            resource_type="setup_report",
            resource_id=setup_report_id,
        )
        return self._repository.get_report(setup_report_id)

    def list_reports(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[SetupReport]:
        """List setup reports."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.report.read",
            scope,
            resource_type="setup_report",
        )
        return self._repository.list_reports(status=status, limit=limit)

    def latest_status(self, scope: list[str] | None = None) -> dict[str, Any]:
        """Return latest setup status for operator cards."""
        return self._repository.status(scope)


__all__ = ["SetupReportService"]
