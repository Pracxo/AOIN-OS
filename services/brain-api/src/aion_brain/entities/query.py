"""Entity query service."""

from __future__ import annotations

from aion_brain.contracts.entities import EntityQuery, EntityQueryResult
from aion_brain.entities.service import EntityService


class EntityQueryService:
    """Small query facade for integrations that should not see repositories."""

    def __init__(self, entity_service: EntityService) -> None:
        self._entity_service = entity_service

    def query(self, query: EntityQuery) -> EntityQueryResult:
        """Query canonical entities."""
        return self._entity_service.query(query)
