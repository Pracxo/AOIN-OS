"""Run supervision report service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.run_supervision import (
    RunSupervisionReport,
    RunSupervisionReportRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class RunSupervisionReportService:
    """Generate read-only run supervision reports."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RunSupervisionReportService:
        return RunSupervisionReportService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def generate(self, request: RunSupervisionReportRequest) -> RunSupervisionReport:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.report.create",
            resource_type="run_supervision_report",
            resource_id=request.trace_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.created_by or self._actor_context.actor_id,
            risk_level="low",
        )
        list_runs = getattr(self._repository, "list_runs", None)
        runs = (
            list_runs(
                scope=request.owner_scope, include_deleted=request.include_archived, limit=1000
            )
            if callable(list_runs)
            else []
        )
        if request.target_systems:
            runs = [run for run in runs if run.target_system in set(request.target_systems)]
        list_controls = getattr(self._repository, "list_control_requests", None)
        controls = list_controls(limit=1000) if callable(list_controls) else []
        list_plans = getattr(self._repository, "list_compensation_plans", None)
        plans = list_plans(scope=request.owner_scope, limit=1000) if callable(list_plans) else []
        stalled = [run for run in runs if run.stalled or run.status == "stalled"]
        failed = [run for run in runs if run.status == "failed"]
        timed_out = [run for run in runs if run.status == "timed_out"]
        recommendations = _recommendations(runs, stalled, failed, timed_out)
        report = RunSupervisionReport(
            supervision_report_id=f"run-supervision-report-{uuid4().hex}",
            trace_id=request.trace_id,
            status="failed" if timed_out else ("warning" if stalled or failed else "passed"),
            owner_scope=request.owner_scope,
            target_systems=request.target_systems,
            run_count=len(runs),
            active_count=sum(1 for run in runs if run.status == "active"),
            completed_count=sum(1 for run in runs if run.status == "completed"),
            failed_count=len(failed),
            stalled_count=len(stalled),
            timeout_count=len(timed_out),
            control_request_count=len(controls),
            compensation_plan_count=len(plans),
            findings=[
                {"type": "stalled_runs", "count": len(stalled)},
                {"type": "failed_runs", "count": len(failed)},
                {"type": "timed_out_runs", "count": len(timed_out)},
            ],
            recommendations=recommendations,
            metadata={**request.metadata, "report_does_not_execute_actions": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_report", None)
        stored = save(report) if callable(save) else report
        emit_telemetry(
            self._telemetry_service,
            event_type="run_supervision_report_created",
            node_type="supervision_report",
            node_id=stored.supervision_report_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "run_count": stored.run_count},
        )
        return stored


def _recommendations(
    runs: list[object], stalled: list[object], failed: list[object], timed_out: list[object]
) -> list[str]:
    recommendations = ["sample_active_runs"] if runs else []
    if stalled:
        recommendations.append("review_stalled_runs")
    if failed:
        recommendations.append("review_failed_runs")
    if timed_out:
        recommendations.extend(["review_timeout_policies", "create_compensation_plan"])
    if failed or timed_out:
        recommendations.append("verify_outcomes")
    return recommendations


__all__ = ["RunSupervisionReportService"]
