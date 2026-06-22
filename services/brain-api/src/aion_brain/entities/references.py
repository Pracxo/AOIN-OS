"""Canonical reference link service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.entities import ReferenceLink, ReferenceLinkCreateRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.entities.repository import EntityRepository


class ReferenceLinkService:
    """Policy-gated reference links across AION-owned records."""

    def __init__(
        self,
        repository: EntityRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        provenance_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._provenance_service = provenance_service

    def create_link(self, request: ReferenceLinkCreateRequest, scope: list[str]) -> ReferenceLink:
        """Create one canonical reference link."""
        authorize(
            self._policy_adapter,
            action_type="entity.reference.create",
            resource_type="reference_link",
            resource_id=request.reference_link_id,
            scope=scope,
            trace_id=request.trace_id,
            risk_level="low",
            context={"relation_type": request.relation_type},
        )
        link = ReferenceLink(
            reference_link_id=request.reference_link_id or f"reference-link-{uuid4().hex}",
            trace_id=request.trace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            target_type=request.target_type,
            target_id=request.target_id,
            relation_type=request.relation_type,
            entity_id=request.entity_id,
            concept_id=request.concept_id,
            confidence=request.confidence,
            evidence_refs=list(request.evidence_refs),
            metadata=dict(request.metadata),
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        stored = self._repository.save_reference_link(link)
        self._record_provenance(stored)
        emit_telemetry(
            self._telemetry_service,
            event_type="reference_link_created",
            node_type="reference",
            node_id=stored.reference_link_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            edge_from=stored.source_id,
            edge_to=stored.target_id,
            payload={"relation_type": stored.relation_type},
        )
        return stored

    def list_links(
        self,
        scope: list[str],
        *,
        entity_id: str | None = None,
        concept_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        limit: int = 100,
    ) -> list[ReferenceLink]:
        """List reference links."""
        authorize(
            self._policy_adapter,
            action_type="entity.reference.read",
            resource_type="reference_link",
            resource_id=entity_id or concept_id or source_id or target_id,
            scope=scope,
        )
        return self._repository.list_reference_links(
            entity_id=entity_id,
            concept_id=concept_id,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            limit=limit,
        )

    def delete_link(self, reference_link_id: str, scope: list[str]) -> ReferenceLink:
        """Soft-delete a reference link."""
        link = self._repository.get_reference_link(reference_link_id)
        if link is None:
            raise ValueError("reference_link_not_found")
        authorize(
            self._policy_adapter,
            action_type="entity.reference.delete",
            resource_type="reference_link",
            resource_id=reference_link_id,
            scope=scope,
            risk_level="medium",
        )
        deleted = link.model_copy(update={"deleted_at": datetime.now(UTC)})
        return self._repository.save_reference_link(deleted)

    def _record_provenance(self, link: ReferenceLink) -> None:
        create = getattr(self._provenance_service, "create_link", None)
        if not callable(create):
            return
        try:
            create(
                source_type=link.source_type,
                source_id=link.source_id,
                target_type=link.target_type,
                target_id=link.target_id,
                trace_id=link.trace_id,
                relation_type=link.relation_type,
                metadata={"reference_link_id": link.reference_link_id},
            )
        except Exception:
            return
