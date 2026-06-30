"""Connector policy audit helpers."""

from __future__ import annotations

from aion_brain.audit_integrity.ledger import record_connector_policy_audit


class ConnectorPolicyAuditService:
    """Record connector policy dry-run audit events without storing connector material."""

    def __init__(self, *, audit_sink: object | None = None) -> None:
        self._audit_sink = audit_sink

    def record_dry_run(
        self,
        *,
        dry_run_id: str,
        trace_id: str | None,
        actor_id: str | None,
        owner_scope: list[str],
        status: str,
    ) -> None:
        """Record one best-effort policy dry-run audit event."""

        record_connector_policy_audit(
            self._audit_sink,
            dry_run_id=dry_run_id,
            trace_id=trace_id,
            actor_id=actor_id,
            owner_scope=owner_scope,
            status=status,
        )


__all__ = ["ConnectorPolicyAuditService"]
