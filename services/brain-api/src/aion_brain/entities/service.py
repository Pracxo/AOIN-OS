"""Canonical entity lifecycle service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.entities import (
    EntityCreateRequest,
    EntityDeleteRequest,
    EntityQuery,
    EntityQueryResult,
    EntityRecord,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.entities.normalizer import normalize_entity_name
from aion_brain.entities.repository import EntityRepository


class EntityService:
    """Policy-gated canonical entity registry."""

    def __init__(
        self,
        repository: EntityRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create(self, request: EntityCreateRequest) -> EntityRecord:
        """Create or return one canonical entity."""
        authorize(
            self._policy_adapter,
            action_type="entity.create",
            resource_type="entity",
            resource_id=request.entity_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.created_by,
            risk_level="low",
            context={"entity_type": request.entity_type},
        )
        normalized = normalize_entity_name(request.canonical_name)
        duplicate = self._repository.find_entity_by_normalized_name(
            normalized,
            request.owner_scope,
        )
        if duplicate is not None:
            return duplicate
        now = datetime.now(UTC)
        entity = EntityRecord(
            entity_id=request.entity_id or f"entity-{uuid4().hex}",
            trace_id=request.trace_id,
            canonical_name=request.canonical_name,
            normalized_name=normalized,
            entity_type=request.entity_type,
            status="active",
            owner_scope=request.owner_scope,
            concept_refs=list(request.concept_refs),
            evidence_refs=list(request.evidence_refs),
            memory_refs=list(request.memory_refs),
            belief_refs=list(request.belief_refs),
            graph_refs=list(request.graph_refs),
            confidence=request.confidence,
            sensitivity=request.sensitivity,
            metadata=dict(request.metadata),
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            merged_into_entity_id=None,
            archived_at=None,
            deleted_at=None,
        )
        stored = self._repository.save_entity(entity)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_created",
            node_type="entity",
            node_id=stored.entity_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={
                "entity_type": stored.entity_type,
                "status": stored.status,
                "owner_scope": stored.owner_scope,
            },
        )
        return stored

    def get(self, entity_id: str, scope: list[str]) -> EntityRecord | None:
        """Return one entity visible to scope."""
        authorize(
            self._policy_adapter,
            action_type="entity.read",
            resource_type="entity",
            resource_id=entity_id,
            scope=scope,
        )
        entity = self._repository.get_entity(entity_id)
        if entity is None or not _scope_matches(entity.owner_scope, scope):
            return None
        return entity

    def query(self, query: EntityQuery) -> EntityQueryResult:
        """Query entities visible to scope."""
        authorize(
            self._policy_adapter,
            action_type="entity.read",
            resource_type="entity",
            resource_id=None,
            scope=query.scope,
            context={"query": bool(query.query)},
        )
        return self._repository.query_entities(query)

    def archive(
        self,
        entity_id: str,
        scope: list[str],
        request: EntityDeleteRequest,
    ) -> EntityRecord:
        """Archive an entity without hard deletion."""
        entity = self.get(entity_id, scope)
        if entity is None:
            raise ValueError("entity_not_found")
        authorize(
            self._policy_adapter,
            action_type="entity.update",
            resource_type="entity",
            resource_id=entity_id,
            scope=scope,
            actor_id=request.actor_id,
            risk_level="medium",
            context={"reason": request.reason},
        )
        archived = entity.model_copy(
            update={
                "status": "archived",
                "updated_at": datetime.now(UTC),
                "archived_at": datetime.now(UTC),
                "metadata": {**entity.metadata, "archive_reason": request.reason},
            }
        )
        stored = self._repository.save_entity(archived)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_archived",
            node_type="entity",
            node_id=stored.entity_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"reason": request.reason},
        )
        return stored

    def soft_delete(
        self,
        entity_id: str,
        scope: list[str],
        request: EntityDeleteRequest,
    ) -> EntityRecord:
        """Soft-delete an entity while preserving the ledger record."""
        entity = self.get(entity_id, scope)
        if entity is None:
            raise ValueError("entity_not_found")
        authorize(
            self._policy_adapter,
            action_type="entity.delete",
            resource_type="entity",
            resource_id=entity_id,
            scope=scope,
            actor_id=request.actor_id,
            risk_level="medium",
            context={"reason": request.reason},
        )
        deleted = entity.model_copy(
            update={
                "status": "archived",
                "updated_at": datetime.now(UTC),
                "deleted_at": datetime.now(UTC),
                "metadata": {**entity.metadata, "delete_reason": request.reason},
            }
        )
        stored = self._repository.save_entity(deleted)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_deleted",
            node_type="entity",
            node_id=stored.entity_id,
            intensity=0.3,
            trace_id=stored.trace_id,
            payload={"soft_deleted": True},
        )
        return stored


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))
