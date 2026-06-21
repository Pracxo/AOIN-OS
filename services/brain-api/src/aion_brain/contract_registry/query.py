"""Read-side query helpers for Contract Registry."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.compatibility import CompatibilityScan, InterfaceDriftFinding
from aion_brain.contracts.contract_registry import (
    ContractIndexRecord,
    ContractRegistryReport,
    ContractSnapshot,
    InterfaceInventoryRecord,
    MigrationNote,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize


class ContractRegistryQueryService:
    """Policy-gated read-side query service."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ContractRegistryQueryService:
        return ContractRegistryQueryService(
            self._repository,
            self._policy_adapter,
            actor_context=actor_context,
        )

    def get_scan(self, compatibility_scan_id: str) -> CompatibilityScan | None:
        self._authorize(
            "contract_registry.compatibility.scan", ["workspace:main"], compatibility_scan_id
        )
        get = getattr(self._repository, "get_scan", None)
        scan = get(compatibility_scan_id) if callable(get) else None
        return scan if isinstance(scan, CompatibilityScan) else None

    def list_findings(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        breaking: bool | None = None,
        interface_type: str | None = None,
        limit: int = 100,
    ) -> list[InterfaceDriftFinding]:
        self._authorize("contract_registry.finding.read", ["workspace:main"], None)
        list_items = getattr(self._repository, "list_findings", None)
        findings = (
            list_items(
                status=status,
                severity=severity,
                breaking=breaking,
                interface_type=interface_type,
                limit=limit,
            )
            if callable(list_items)
            else []
        )
        return [item for item in findings if isinstance(item, InterfaceDriftFinding)]

    def dismiss_finding(
        self,
        drift_finding_id: str,
        actor_id: str | None,
        reason: str,
    ) -> InterfaceDriftFinding:
        get = getattr(self._repository, "get_finding", None)
        finding = get(drift_finding_id) if callable(get) else None
        if not isinstance(finding, InterfaceDriftFinding):
            raise ValueError("drift_finding_not_found")
        self._authorize("contract_registry.finding.update", ["workspace:main"], drift_finding_id)
        updated = finding.model_copy(
            update={
                "status": "dismissed",
                "dismissed_at": datetime.now(UTC),
                "metadata": {**finding.metadata, "dismiss_reason": reason, "actor_id": actor_id},
            }
        )
        save = getattr(self._repository, "save_finding", None)
        stored = save(updated) if callable(save) else updated
        return stored if isinstance(stored, InterfaceDriftFinding) else updated

    def latest_report(self) -> ContractRegistryReport | None:
        self._authorize("contract_registry.report.read", ["workspace:main"], None)
        latest = getattr(self._repository, "latest_report", None)
        report = latest() if callable(latest) else None
        return report if isinstance(report, ContractRegistryReport) else None

    def _authorize(self, action_type: str, scope: list[str], resource_id: str | None) -> None:
        authorize(
            self._policy_adapter,
            action_type=action_type,
            resource_type="contract_registry",
            resource_id=resource_id,
            scope=scope or self._actor_context.security_scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )


__all__ = [
    "ContractRegistryQueryService",
    "CompatibilityScan",
    "ContractIndexRecord",
    "ContractRegistryReport",
    "ContractSnapshot",
    "InterfaceDriftFinding",
    "InterfaceInventoryRecord",
    "MigrationNote",
]
