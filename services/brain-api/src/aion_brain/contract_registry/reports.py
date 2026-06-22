"""Contract registry report service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.compatibility import CompatibilityScan, InterfaceDriftFinding
from aion_brain.contracts.contract_registry import (
    ContractRegistryReport,
    ContractSnapshot,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ContractRegistryReportService:
    """Generate deterministic contract registry health reports."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ContractRegistryReportService:
        return ContractRegistryReportService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            actor_context=actor_context,
        )

    def generate(
        self,
        scope: list[str],
        trace_id: str | None = None,
        created_by: str | None = None,
    ) -> ContractRegistryReport:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.report.create",
            resource_type="contract_report",
            resource_id=None,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        latest_snapshot = _latest_snapshot(self._repository)
        latest_scan = _latest_scan(self._repository)
        findings = _active_findings(self._repository)
        breaking = [item for item in findings if item.breaking]
        warnings = [item for item in findings if not item.breaking]
        missing_sdk = [item for item in findings if item.finding_type == "missing_sdk_binding"]
        missing_cli = [item for item in findings if item.finding_type == "missing_cli_binding"]
        missing_policy = [item for item in findings if item.finding_type == "missing_policy_action"]
        deprecated_count = _deprecated_count(self._repository)
        report = ContractRegistryReport(
            contract_report_id=f"contract-report-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            status="failed" if breaking else "warning" if warnings else "passed",
            owner_scope=scope,
            snapshot_id=latest_snapshot.contract_snapshot_id if latest_snapshot else None,
            latest_scan_id=latest_scan.compatibility_scan_id if latest_scan else None,
            contract_count=latest_snapshot.contract_count if latest_snapshot else 0,
            interface_count=latest_snapshot.interface_count if latest_snapshot else 0,
            active_breaking_findings=len(breaking),
            active_warning_findings=len(warnings),
            deprecated_count=deprecated_count,
            missing_sdk_count=len(missing_sdk),
            missing_cli_count=len(missing_cli),
            missing_policy_count=len(missing_policy),
            findings=[item.model_dump(mode="json") for item in findings[:100]],
            recommendations=_recommendations(latest_snapshot is None, findings),
            metadata={"source_mutated": False, "code_generated": False},
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_report", None)
        stored = save(report) if callable(save) else report
        _record_audit(
            self._audit_sink, "contract_registry_report_created", stored.contract_report_id
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="contract_registry_report_created",
            node_type="contract_report",
            node_id=stored.contract_report_id,
            intensity=1.0 if stored.active_breaking_findings else 0.5,
            trace_id=stored.trace_id,
            payload={"status": stored.status},
        )
        return stored


def _latest_snapshot(repository: object) -> ContractSnapshot | None:
    latest = getattr(repository, "latest_snapshot", None)
    snapshot = latest() if callable(latest) else None
    return snapshot if isinstance(snapshot, ContractSnapshot) else None


def _latest_scan(repository: object) -> CompatibilityScan | None:
    latest = getattr(repository, "latest_scan", None)
    scan = latest() if callable(latest) else None
    return scan if isinstance(scan, CompatibilityScan) else None


def _active_findings(repository: object) -> list[InterfaceDriftFinding]:
    list_findings = getattr(repository, "list_findings", None)
    findings = list_findings(status="open", limit=1000) if callable(list_findings) else []
    return [item for item in findings if isinstance(item, InterfaceDriftFinding)]


def _deprecated_count(repository: object) -> int:
    list_contracts = getattr(repository, "list_contracts", None)
    list_interfaces = getattr(repository, "list_interfaces", None)
    contracts = list_contracts(status="deprecated", limit=1000) if callable(list_contracts) else []
    interfaces = (
        list_interfaces(status="deprecated", limit=1000) if callable(list_interfaces) else []
    )
    return len(contracts) + len(interfaces)


def _recommendations(snapshot_missing: bool, findings: list[InterfaceDriftFinding]) -> list[str]:
    recommendations: list[str] = []
    if snapshot_missing:
        recommendations.append("run_contract_snapshot")
    recommendations.append("run_compatibility_scan")
    if any(item.finding_type == "missing_sdk_binding" for item in findings):
        recommendations.append("add_sdk_binding")
    if any(item.finding_type == "missing_cli_binding" for item in findings):
        recommendations.append("add_cli_command")
    if any(item.finding_type == "missing_policy_action" for item in findings):
        recommendations.append("add_policy_action")
    if any(item.breaking for item in findings):
        recommendations.append("resolve_breaking_findings")
        recommendations.append("update_migration_notes")
    recommendations.append("update_docs")
    return list(dict.fromkeys(recommendations))


def _record_audit(audit_sink: object | None, event_type: str, resource_id: str) -> None:
    record = getattr(audit_sink, "record", None) or getattr(audit_sink, "record_event", None)
    if callable(record):
        try:
            record(event_type=event_type, resource_id=resource_id)
        except Exception:
            return


__all__ = ["ContractRegistryReportService"]
