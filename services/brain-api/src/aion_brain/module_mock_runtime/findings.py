"""Module mock finding service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.module_mock_runtime import (
    ModuleMockFinding,
    ModuleMockFindingDismissRequest,
)
from aion_brain.module_mock_runtime.policy import authorize_module_mock_action
from aion_brain.module_mock_runtime.repository import ModuleMockRuntimeRepository


class ModuleMockFindingService:
    """Read and dismiss module mock runtime findings."""

    def __init__(self, repository: ModuleMockRuntimeRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def list_findings(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        capability_binding_id: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockFinding]:
        """List findings after policy authorization."""

        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.finding.read",
            scope,
            resource_type="module_mock_finding",
            risk_level="low",
        )
        return self._repository.list_findings(
            capability_binding_id=capability_binding_id,
            status=status,
            severity=severity,
            limit=limit,
        )

    def dismiss_finding(
        self,
        module_mock_finding_id: str,
        scope: list[str],
        request: ModuleMockFindingDismissRequest,
    ) -> ModuleMockFinding:
        """Dismiss a finding without changing the source run."""

        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.finding.update",
            scope,
            actor_id=request.actor_id,
            resource_type="module_mock_finding",
            resource_id=module_mock_finding_id,
            risk_level="medium",
            context={"reason": request.reason},
        )
        finding = self._repository.get_finding(module_mock_finding_id)
        if finding is None:
            raise AIONNotFoundException("module_mock_finding_not_found")
        return self._repository.save_finding(
            finding.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {**finding.metadata, "dismiss_reason": request.reason},
                }
            )
        )


__all__ = ["ModuleMockFindingService"]
