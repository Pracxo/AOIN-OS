"""Generic provenance link service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.contracts.audit_integrity import ProvenanceLink
from aion_brain.contracts.policy import PolicyRequest

LOCAL_SESSION_PROVENANCE_BOUNDARY = {
    "source_component": "local_session",
    "local_only": True,
    "read_only": True,
    "auth_material_stored": False,
    "session_state_stored": False,
}


class ProvenanceService:
    """Create, query, and soft-delete provenance links."""

    def __init__(
        self,
        repository: AuditIntegrityRepository,
        policy_adapter: object | None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def create_link(self, link: ProvenanceLink) -> ProvenanceLink:
        """Create one provenance link through policy."""
        self._authorize("audit.provenance.write", link.trace_id, "provenance", link.source_id)
        stored = self._repository.save_provenance_link(
            link.model_copy(update={"created_at": link.created_at or datetime.now(UTC)})
        )
        record_audit_event(
            self._audit_sink,
            action_type="audit.provenance.write",
            resource_type="provenance",
            resource_id=stored.provenance_link_id,
            event_type="provenance_link_created",
            outcome="completed",
            source_component="provenance_service",
            trace_id=stored.trace_id,
            payload={
                "source_type": stored.source_type,
                "target_type": stored.target_type,
                "relation_type": stored.relation_type,
            },
        )
        return stored

    def list_links(
        self,
        *,
        source_type: str | None = None,
        source_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> list[ProvenanceLink]:
        """List provenance links through policy."""
        self._authorize("audit.provenance.read", trace_id, "provenance", trace_id)
        return self._repository.list_provenance_links(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            trace_id=trace_id,
            limit=limit,
        )

    def graph_for_trace(self, trace_id: str, limit: int = 500) -> list[ProvenanceLink]:
        """Return provenance links for a trace."""
        self._authorize("audit.provenance.read", trace_id, "trace", trace_id)
        return self._repository.list_provenance_links(trace_id=trace_id, limit=limit)

    def soft_delete_link(
        self,
        provenance_link_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft-delete one provenance link."""
        self._authorize(
            "audit.provenance.delete",
            None,
            "provenance",
            provenance_link_id,
            actor_id=actor_id,
            risk_level="medium",
        )
        link = self._repository.get_provenance_link(provenance_link_id)
        if link is None:
            return False
        metadata = {**link.metadata, "deleted_by": actor_id, "delete_reason": reason}
        deleted = self._repository.soft_delete_provenance_link(
            provenance_link_id,
            deleted_at=datetime.now(UTC),
            metadata=metadata,
        )
        if deleted:
            record_audit_event(
                self._audit_sink,
                action_type="audit.provenance.delete",
                resource_type="provenance",
                resource_id=provenance_link_id,
                event_type="provenance_link_deleted",
                outcome="completed",
                source_component="provenance_service",
                actor_id=actor_id,
                trace_id=link.trace_id,
                payload={"reason": reason},
            )
        return deleted

    def _authorize(
        self,
        action_type: str,
        trace_id: str | None,
        resource_type: str,
        resource_id: str | None,
        *,
        actor_id: str | None = None,
        risk_level: str = "low",
    ) -> None:
        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return
        decision = authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or 'all'}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=["workspace:main"],
                context={},
            )
        )
        if not bool(getattr(decision, "allow", False)):
            raise PermissionError(str(getattr(decision, "reason", "policy_denied")))
