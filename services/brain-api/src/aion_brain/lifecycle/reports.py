"""Lifecycle report service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.lifecycle import LifecycleReport, LifecycleReportStatus
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

_RECOMMENDATIONS = [
    "run_lifecycle_evaluation",
    "review_archive_candidates",
    "review_redaction_candidates",
    "verify_backup_before_archive",
    "inspect_purge_preview_blockers",
    "review_sensitive_resources",
    "run_registry_validation",
]


class LifecycleReportService:
    """Generate local deterministic lifecycle reports."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        registry_repository: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._registry_repository = registry_repository
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> LifecycleReportService:
        return LifecycleReportService(
            self._repository,
            self._policy_adapter,
            registry_repository=self._registry_repository,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def generate(
        self,
        scope: list[str],
        trace_id: str | None = None,
        created_by: str | None = None,
    ) -> LifecycleReport:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.report.create",
            resource_type="lifecycle_report",
            resource_id=None,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        resources = _list_registry_resources(self._registry_repository, scope)
        classifications = _list(self._repository, "list_classifications", scope)
        archives = _list(self._repository, "list_archive_candidates", scope)
        redactions = _list(self._repository, "list_redaction_candidates", scope)
        previews = _list(self._repository, "list_purge_previews", scope)
        sensitive_count = sum(
            1
            for item in [*resources, *classifications]
            if str(getattr(getattr(item, "descriptor", item), "sensitivity", ""))
            in {"confidential", "restricted"}
        )
        overdue_count = sum(
            1 for item in classifications if getattr(item, "lifecycle_state", "") == "review_due"
        )
        findings = []
        if archives:
            findings.append({"type": "archive_candidates", "count": len(archives)})
        if redactions:
            findings.append({"type": "redaction_candidates", "count": len(redactions)})
        if previews:
            findings.append({"type": "purge_previews", "count": len(previews)})
        status: LifecycleReportStatus = "warning" if findings else "passed"
        report = LifecycleReport(
            lifecycle_report_id=f"lifecycle-report-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            status=status,
            owner_scope=scope,
            resource_count=len(resources),
            classified_count=len(classifications),
            archive_candidate_count=len(archives),
            redaction_candidate_count=len(redactions),
            purge_preview_count=len(previews),
            overdue_review_count=overdue_count,
            sensitive_resource_count=sensitive_count,
            findings=findings,
            recommendations=_RECOMMENDATIONS,
            metadata={"source_records_mutated": False},
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_report(self._repository, report)
        emit_telemetry(
            self._telemetry_service,
            event_type="lifecycle_report_created",
            node_type="lifecycle_report",
            node_id=stored.lifecycle_report_id,
            intensity=0.6 if stored.status == "passed" else 0.85,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "findings": len(stored.findings)},
        )
        return stored

    def status(self, scope: list[str]) -> dict[str, object]:
        latest = _latest_report(self._repository, scope)
        if latest is None:
            return {"status": "warning", "message": "No lifecycle report available."}
        return {
            "status": latest.status,
            "resource_count": latest.resource_count,
            "findings": len(latest.findings),
        }

    def latest_report(self, scope: list[str]) -> LifecycleReport | None:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.report.read",
            resource_type="lifecycle_report",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        return _latest_report(self._repository, scope)


def _list(repository: object, method_name: str, scope: list[str]) -> list[object]:
    method = getattr(repository, method_name, None)
    return list(method(scope, limit=1000) or []) if callable(method) else []


def _list_registry_resources(registry_repository: object | None, scope: list[str]) -> list[object]:
    method = getattr(registry_repository, "list_resources", None)
    if not callable(method):
        return []
    try:
        from aion_brain.contracts.resource_registry import ResourceRegistryQuery

        return list(method(ResourceRegistryQuery(scope=scope, limit=1000)) or [])
    except Exception:
        return []


def _save_report(repository: object, report: LifecycleReport) -> LifecycleReport:
    save = getattr(repository, "save_report", None)
    stored = save(report) if callable(save) else report
    return stored if isinstance(stored, LifecycleReport) else report


def _latest_report(repository: object, scope: list[str]) -> LifecycleReport | None:
    latest = getattr(repository, "latest_report", None)
    report = latest(scope) if callable(latest) else None
    return report if isinstance(report, LifecycleReport) else None


__all__ = ["LifecycleReportService"]
