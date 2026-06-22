"""Best-effort audit and provenance helpers for grounding services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.audit_integrity import ProvenanceLink
from aion_brain.contracts.scopes import ActorContext


def record_grounding_audit(
    audit_sink: object | None,
    *,
    action_type: str,
    resource_type: str,
    resource_id: str | None,
    event_type: str,
    trace_id: str | None,
    actor_context: ActorContext,
    payload: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Record one grounding audit entry without breaking the caller."""

    entry = record_audit_event(
        audit_sink,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        event_type=event_type,
        outcome="completed",
        source_component="grounding_manager",
        trace_id=trace_id or actor_context.trace_id,
        actor_id=actor_context.actor_id,
        workspace_id=actor_context.workspace_id,
        risk_level="low",
        payload=payload or {},
        metadata=metadata or {},
    )
    return entry.audit_entry_id if entry is not None else None


def create_grounding_provenance_link(
    provenance_service: object | None,
    *,
    source_type: str,
    source_id: str | None,
    target_type: str,
    target_id: str | None,
    trace_id: str | None,
    relation_type: str = "referenced",
    evidence_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    audit_entry_id: str | None = None,
) -> None:
    """Create one provenance link without breaking the caller."""

    if not source_id or not target_id:
        return
    create_link = getattr(provenance_service, "create_link", None)
    if not callable(create_link):
        return
    try:
        create_link(
            ProvenanceLink(
                provenance_link_id=f"provenance-{uuid4().hex}",
                trace_id=trace_id,
                source_type=cast(Any, source_type),
                source_id=source_id,
                target_type=cast(Any, target_type),
                target_id=target_id,
                relation_type=cast(Any, relation_type),
                confidence=1.0,
                audit_entry_id=audit_entry_id,
                evidence_refs=evidence_refs or [],
                metadata=metadata or {},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return


__all__ = ["create_grounding_provenance_link", "record_grounding_audit"]
