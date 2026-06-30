"""Connector credential audit helpers."""

from __future__ import annotations

from aion_brain.audit_integrity.ledger import record_connector_credential_readiness_audit


class ConnectorCredentialAuditService:
    """Record connector credential readiness audit events without material."""

    def __init__(self, *, audit_sink: object | None = None) -> None:
        self._audit_sink = audit_sink

    def record_readiness(
        self,
        *,
        readiness_id: str,
        trace_id: str | None,
        actor_id: str | None,
        owner_scope: list[str],
        status: str,
    ) -> None:
        """Record one best-effort credential readiness audit event."""

        record_connector_credential_readiness_audit(
            self._audit_sink,
            readiness_id=readiness_id,
            trace_id=trace_id,
            actor_id=actor_id,
            owner_scope=owner_scope,
            status=status,
        )


__all__ = ["ConnectorCredentialAuditService"]
