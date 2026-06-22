"""Concept registry service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.concepts.normalizer import normalize_concept_name
from aion_brain.concepts.repository import ConceptRepository
from aion_brain.contracts.concepts import ConceptCreateRequest, ConceptRecord
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ConceptService:
    """Policy-gated concept registry."""

    def __init__(
        self,
        repository: ConceptRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create(self, request: ConceptCreateRequest) -> ConceptRecord:
        """Create or return one active concept."""
        authorize(
            self._policy_adapter,
            action_type="concept.create",
            resource_type="concept",
            resource_id=request.concept_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.created_by,
            risk_level="low",
            context={"concept_type": request.concept_type},
        )
        normalized = normalize_concept_name(request.name)
        duplicate = self._repository.find_by_normalized_name(normalized, request.owner_scope)
        if duplicate is not None:
            return duplicate
        now = datetime.now(UTC)
        concept = ConceptRecord(
            concept_id=request.concept_id or f"concept-{uuid4().hex}",
            trace_id=request.trace_id,
            name=request.name,
            normalized_name=normalized,
            concept_type=request.concept_type,
            status="active",
            description=request.description,
            owner_scope=request.owner_scope,
            aliases=[normalize_concept_name(alias) for alias in request.aliases],
            metadata=dict(request.metadata),
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            archived_at=None,
        )
        stored = self._repository.save(concept)
        emit_telemetry(
            self._telemetry_service,
            event_type="concept_created",
            node_type="concept",
            node_id=stored.concept_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            payload={"concept_type": stored.concept_type, "owner_scope": stored.owner_scope},
        )
        return stored

    def get(self, concept_id: str, scope: list[str]) -> ConceptRecord | None:
        """Return one concept visible to scope."""
        authorize(
            self._policy_adapter,
            action_type="concept.read",
            resource_type="concept",
            resource_id=concept_id,
            scope=scope,
        )
        concept = self._repository.get(concept_id)
        if concept is None or not _scope_matches(concept.owner_scope, scope):
            return None
        return concept

    def list_concepts(
        self,
        *,
        scope: list[str],
        query: str | None = None,
        concept_types: list[str] | None = None,
        status: str | None = "active",
        limit: int = 100,
    ) -> list[ConceptRecord]:
        """List concepts visible to scope."""
        authorize(
            self._policy_adapter,
            action_type="concept.read",
            resource_type="concept",
            resource_id=None,
            scope=scope,
        )
        return self._repository.list_concepts(
            scope=scope,
            query=normalize_concept_name(query) if query else None,
            concept_types=concept_types,
            status=status,
            limit=limit,
        )

    def archive(
        self,
        concept_id: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        reason: str,
    ) -> ConceptRecord:
        """Archive one concept."""
        concept = self.get(concept_id, scope)
        if concept is None:
            raise ValueError("concept_not_found")
        authorize(
            self._policy_adapter,
            action_type="concept.update",
            resource_type="concept",
            resource_id=concept_id,
            scope=scope,
            actor_id=actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        archived = concept.model_copy(
            update={
                "status": "archived",
                "updated_at": datetime.now(UTC),
                "archived_at": datetime.now(UTC),
                "metadata": {**concept.metadata, "archive_reason": reason},
            }
        )
        stored = self._repository.save(archived)
        emit_telemetry(
            self._telemetry_service,
            event_type="concept_archived",
            node_type="concept",
            node_id=stored.concept_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"reason": reason},
        )
        return stored


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))
