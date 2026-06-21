"""Scheduler report builder."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.scheduler import SchedulerReport, SchedulerReportStatus
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.scheduler.policy_context import scheduler_policy_context


class SchedulerReportService:
    """Build and persist read-only scheduler reports."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_report(
        self,
        scope: list[str],
        *,
        trace_id: str | None = None,
        workspace_id: str | None = None,
    ) -> SchedulerReport:
        authorize(
            self._policy_adapter,
            action_type="scheduler.report.create",
            resource_type="scheduler_report",
            resource_id=None,
            scope=scope,
            trace_id=trace_id,
            workspace_id=workspace_id,
            risk_level="low",
            context=scheduler_policy_context(
                "scheduler.report.create",
                scope,
                workspace_id=workspace_id,
            ),
        )
        schedules = _list(
            self._repository, "list_schedules", scope=scope, status="active", limit=1000
        )
        due_items = _list(self._repository, "list_due_items", scope=scope, status="due", limit=1000)
        reminders = _list(self._repository, "list_reminders", scope=scope, status="due", limit=1000)
        missed = _list(self._repository, "list_due_items", scope=scope, status="missed", limit=1000)
        failed_ticks = _list(
            self._repository, "list_tick_runs", scope=scope, status="failed", limit=1000
        )
        findings: list[str] = []
        if missed:
            findings.append("missed_schedule_items_present")
        if failed_ticks:
            findings.append("failed_scheduler_ticks_present")
        status: SchedulerReportStatus = (
            "failed" if failed_ticks else ("warning" if missed else "passed")
        )
        report = SchedulerReport(
            report_id=f"scheduler-report-{uuid4().hex}",
            trace_id=trace_id,
            workspace_id=workspace_id,
            owner_scope=scope,
            status=status,
            title="Scheduler Local Readiness",
            summary="Local scheduler records were inspected without executing targets.",
            active_schedule_count=len(schedules),
            due_item_count=len(due_items),
            reminder_count=len(reminders),
            missed_schedule_count=len(missed),
            failed_tick_count=len(failed_ticks),
            findings=findings,
            recommendations=["review_due_items"] if due_items else [],
            metadata={"local_only": True, "no_target_execution": True},
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_report", None)
        stored = save(report) if callable(save) else report
        result = stored if isinstance(stored, SchedulerReport) else report
        emit_telemetry(
            self._telemetry_service,
            event_type="scheduler_report_created",
            node_type="scheduler_report",
            node_id=result.report_id,
            intensity=0.55 if result.status == "passed" else 0.85,
            trace_id=result.trace_id,
            payload={"owner_scope": result.owner_scope, "status": result.status},
        )
        return result

    def list_reports(
        self, scope: list[str], *, status: str | None = None, limit: int = 100
    ) -> list[SchedulerReport]:
        authorize(
            self._policy_adapter,
            action_type="scheduler.report.read",
            resource_type="scheduler_report",
            resource_id=None,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context("scheduler.report.read", scope),
        )
        result = _list(self._repository, "list_reports", scope=scope, status=status, limit=limit)
        return [item for item in result if isinstance(item, SchedulerReport)]


def _list(repository: object, method_name: str, **kwargs: object) -> list[object]:
    method = getattr(repository, method_name, None)
    if not callable(method):
        return []
    try:
        result = method(**kwargs)
    except TypeError:
        return []
    return result if isinstance(result, list) else []
