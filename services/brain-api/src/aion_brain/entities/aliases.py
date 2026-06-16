"""Entity alias service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.entities import EntityAlias, EntityAliasCreateRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.entities.normalizer import normalize_entity_name
from aion_brain.entities.repository import EntityRepository


class EntityAliasService:
    """Policy-gated alias management."""

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

    def add_alias(self, request: EntityAliasCreateRequest, scope: list[str]) -> EntityAlias:
        """Add one alias to an entity."""
        entity = self._repository.get_entity(request.entity_id)
        if entity is None or not _scope_matches(entity.owner_scope, scope):
            raise ValueError("entity_not_found")
        authorize(
            self._policy_adapter,
            action_type="entity.alias.create",
            resource_type="entity_alias",
            resource_id=request.alias_id,
            scope=scope,
            risk_level="low",
            context={"entity_id": request.entity_id, "alias_type": request.alias_type},
        )
        alias = EntityAlias(
            alias_id=request.alias_id or f"entity-alias-{uuid4().hex}",
            entity_id=request.entity_id,
            alias=request.alias,
            normalized_alias=normalize_entity_name(request.alias),
            alias_type=request.alias_type,
            confidence=request.confidence,
            source_type=request.source_type,
            source_id=request.source_id,
            metadata=dict(request.metadata),
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        stored = self._repository.save_alias(alias)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_alias_added",
            node_type="entity",
            node_id=stored.entity_id,
            intensity=stored.confidence,
            trace_id=entity.trace_id,
            payload={"alias_id": stored.alias_id, "alias_type": stored.alias_type},
        )
        return stored

    def list_aliases(self, entity_id: str, scope: list[str]) -> list[EntityAlias]:
        """List aliases for an entity."""
        entity = self._repository.get_entity(entity_id)
        if entity is None or not _scope_matches(entity.owner_scope, scope):
            raise ValueError("entity_not_found")
        authorize(
            self._policy_adapter,
            action_type="entity.alias.read",
            resource_type="entity_alias",
            resource_id=entity_id,
            scope=scope,
        )
        return self._repository.list_aliases(entity_ids=[entity_id])

    def delete_alias(self, alias_id: str, scope: list[str]) -> EntityAlias:
        """Soft-delete an alias."""
        alias = self._repository.get_alias(alias_id)
        if alias is None:
            raise ValueError("entity_alias_not_found")
        entity = self._repository.get_entity(alias.entity_id)
        if entity is None or not _scope_matches(entity.owner_scope, scope):
            raise ValueError("entity_not_found")
        authorize(
            self._policy_adapter,
            action_type="entity.alias.delete",
            resource_type="entity_alias",
            resource_id=alias_id,
            scope=scope,
            risk_level="medium",
        )
        deleted = alias.model_copy(update={"deleted_at": datetime.now(UTC)})
        return self._repository.save_alias(deleted)


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))
