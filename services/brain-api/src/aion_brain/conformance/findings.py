"""Conformance finding service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.conformance.policy import authorize_conformance_action
from aion_brain.conformance.repository import ConformanceRepository
from aion_brain.conformance.telemetry import emit_conformance_telemetry
from aion_brain.contracts.conformance import ConformanceFinding


class ConformanceFindingService:
    """List and dismiss conformance-owned findings."""

    def __init__(
        self,
        repository: ConformanceRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def list_findings(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        finding_type: str | None = None,
        limit: int = 100,
    ) -> list[ConformanceFinding]:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.finding.read",
            scope,
            resource_type="conformance_finding",
        )
        return self._repository.list_findings(
            status=status,
            severity=severity,
            finding_type=finding_type,
            limit=limit,
        )

    def dismiss_finding(
        self,
        conformance_finding_id: str,
        scope: list[str],
        actor_id: str | None,
        reason: str,
    ) -> ConformanceFinding:
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.finding.update",
            scope,
            actor_id=actor_id,
            resource_type="conformance_finding",
            resource_id=conformance_finding_id,
            risk_level="medium",
        )
        finding = self._repository.get_finding(conformance_finding_id)
        if finding is None:
            raise AIONNotFoundException("conformance_finding_not_found")
        saved = self._repository.save_finding(
            finding.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {**finding.metadata, "dismiss_reason": reason},
                }
            )
        )
        emit_conformance_telemetry(
            self._telemetry_service,
            event_type="conformance_finding_dismissed",
            node_type="conformance_finding",
            node_id=saved.conformance_finding_id,
            scope=scope,
            intensity=0.3,
            payload={"finding_type": saved.finding_type},
        )
        return saved


__all__ = ["ConformanceFindingService"]
