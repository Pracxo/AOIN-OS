"""Citation service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.citations import CitationCreateRequest, CitationRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.grounding.audit import (
    create_grounding_provenance_link,
    record_grounding_audit,
)
from aion_brain.grounding.redaction import redact_text, sanitize_payload


class CitationService:
    """Create, list, and soft-delete citation records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> CitationService:
        return CitationService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            actor_context=actor_context,
        )

    def create_citation(self, request: CitationCreateRequest) -> CitationRecord:
        """Create a citation after policy authorization."""

        scope = _scope_from_request(request, self._actor_context)
        authorize(
            self._policy_adapter,
            action_type="grounding.citation.create",
            resource_type="citation",
            resource_id=request.citation_id or request.source_id,
            scope=scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
            context={"source_type": request.source_type, "citation_type": request.citation_type},
        )
        citation = CitationRecord(
            citation_id=request.citation_id or f"citation-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            response_id=request.response_id,
            explanation_id=request.explanation_id,
            source_type=request.source_type,
            source_id=request.source_id,
            grounding_source_id=request.grounding_source_id,
            citation_type=request.citation_type,
            label=request.label,
            quote=redact_text(request.quote) if request.quote is not None else None,
            start_char=request.start_char,
            end_char=request.end_char,
            confidence=request.confidence,
            verified=request.verified,
            metadata=sanitize_payload(request.metadata),
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        saved = _save_citation(self._repository, citation)
        emit_telemetry(
            self._telemetry_service,
            event_type="citation_record_created",
            node_type="citation",
            node_id=saved.citation_id,
            intensity=saved.confidence,
            trace_id=saved.trace_id,
            edge_from=saved.grounding_source_id or saved.source_id,
            edge_to=saved.citation_id,
            payload={"citation_type": saved.citation_type, "response_id": saved.response_id},
        )
        audit_entry_id = record_grounding_audit(
            self._audit_sink,
            action_type="grounding.citation.create",
            resource_type="citation",
            resource_id=saved.citation_id,
            event_type="citation_record_created",
            trace_id=saved.trace_id,
            actor_context=self._actor_context,
            payload={
                "citation_type": saved.citation_type,
                "source_type": saved.source_type,
                "source_id": saved.source_id,
                "response_id": saved.response_id,
                "explanation_id": saved.explanation_id,
            },
        )
        _link_citation_provenance(self._provenance_service, saved, audit_entry_id)
        return saved

    def list_citations(
        self,
        response_id: str | None = None,
        explanation_id: str | None = None,
        source_id: str | None = None,
        limit: int = 100,
    ) -> list[CitationRecord]:
        """List active citations."""

        authorize(
            self._policy_adapter,
            action_type="grounding.citation.read",
            resource_type="citation",
            resource_id=response_id or explanation_id or source_id,
            scope=self._actor_context.security_scope or ["workspace:main"],
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        return _list_citations(
            self._repository,
            response_id=response_id,
            explanation_id=explanation_id,
            source_id=source_id,
            limit=limit,
        )

    def soft_delete_citation(
        self,
        citation_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft-delete a citation record after policy authorization."""

        authorize(
            self._policy_adapter,
            action_type="grounding.citation.delete",
            resource_type="citation",
            resource_id=citation_id,
            scope=self._actor_context.security_scope or ["workspace:main"],
            trace_id=self._actor_context.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            approval_present=True,
            context={"reason": reason},
        )
        delete = getattr(self._repository, "soft_delete_citation", None)
        return bool(delete(citation_id)) if callable(delete) else False


def _save_citation(repository: object, citation: CitationRecord) -> CitationRecord:
    save = getattr(repository, "save_citation", None)
    if callable(save):
        result = save(citation)
        if isinstance(result, CitationRecord):
            return result
    return citation


def _list_citations(repository: object, **kwargs: Any) -> list[CitationRecord]:
    list_citations = getattr(repository, "list_citations", None)
    if callable(list_citations):
        result = list_citations(**kwargs)
        if isinstance(result, list):
            return [item for item in result if isinstance(item, CitationRecord)]
    return []


def _scope_from_request(request: CitationCreateRequest, actor_context: ActorContext) -> list[str]:
    raw = request.metadata.get("owner_scope") if isinstance(request.metadata, dict) else None
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    return actor_context.security_scope or ["workspace:main"]


def _link_citation_provenance(
    provenance_service: object | None,
    citation: CitationRecord,
    audit_entry_id: str | None,
) -> None:
    if citation.response_id:
        create_grounding_provenance_link(
            provenance_service,
            source_type="response",
            source_id=citation.response_id,
            target_type="citation",
            target_id=citation.citation_id,
            trace_id=citation.trace_id,
            relation_type="referenced",
            audit_entry_id=audit_entry_id,
        )
    if citation.explanation_id:
        create_grounding_provenance_link(
            provenance_service,
            source_type="explanation",
            source_id=citation.explanation_id,
            target_type="citation",
            target_id=citation.citation_id,
            trace_id=citation.trace_id,
            relation_type="referenced",
            audit_entry_id=audit_entry_id,
        )
    create_grounding_provenance_link(
        provenance_service,
        source_type="citation",
        source_id=citation.citation_id,
        target_type="grounding_source" if citation.grounding_source_id else citation.source_type,
        target_id=citation.grounding_source_id or citation.source_id,
        trace_id=citation.trace_id,
        relation_type="grounded_by",
        audit_entry_id=audit_entry_id,
    )


__all__ = ["CitationService"]
