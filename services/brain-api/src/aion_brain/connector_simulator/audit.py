"""Audit helpers for connector simulator dry runs."""

from __future__ import annotations

from aion_brain.audit_integrity.ledger import record_connector_simulator_audit
from aion_brain.contracts.connector_simulator import ConnectorSimulationResult


class ConnectorSimulatorAuditService:
    """Record safe connector simulator audit/provenance evidence."""

    def __init__(self, audit_sink: object | None = None) -> None:
        self._audit_sink = audit_sink

    def record_simulation(
        self,
        result: ConnectorSimulationResult,
        *,
        created_by: str | None,
        owner_scope: list[str],
    ) -> None:
        """Record a local synthetic simulation audit event."""

        record_connector_simulator_audit(
            self._audit_sink,
            simulation_id=str(result.connector_simulation_result_id),
            trace_id=result.trace_id,
            actor_id=created_by,
            owner_scope=owner_scope,
            status=str(result.status),
        )


__all__ = ["ConnectorSimulatorAuditService"]
