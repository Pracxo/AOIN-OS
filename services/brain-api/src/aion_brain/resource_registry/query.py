"""Query service for registry-owned records."""

from __future__ import annotations

from aion_brain.contracts.resource_registry import (
    ResourceRegistryQuery,
    ResourceRegistryQueryResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize


class RegistryQueryService:
    """Aggregate registry resources, links, and integrity findings."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RegistryQueryService:
        return RegistryQueryService(
            self._repository,
            self._policy_adapter,
            actor_context=actor_context,
        )

    def query(self, query: ResourceRegistryQuery) -> ResourceRegistryQueryResult:
        authorize(
            self._policy_adapter,
            action_type="registry.resource.read",
            resource_type="resource",
            resource_id=None,
            scope=query.scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        resources = []
        list_resources = getattr(self._repository, "list_resources", None)
        if callable(list_resources):
            resources = [record.descriptor for record in list_resources(query)]
        list_links = getattr(self._repository, "list_links", None)
        links = list_links(limit=query.limit) if callable(list_links) else []
        list_broken = getattr(self._repository, "list_broken_references", None)
        broken = list_broken(limit=query.limit) if callable(list_broken) else []
        list_orphans = getattr(self._repository, "list_orphaned_resources", None)
        orphans = list_orphans(limit=query.limit) if callable(list_orphans) else []
        return ResourceRegistryQueryResult(
            resources=resources,
            links=list(links or []),
            broken_references=list(broken or []),
            orphaned_resources=list(orphans or []),
            total_count=len(resources),
            metadata={"registry_is_source_of_truth": False},
        )


__all__ = ["RegistryQueryService"]
