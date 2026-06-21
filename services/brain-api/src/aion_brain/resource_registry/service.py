"""Global Resource Registry service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.resource_registry import (
    ResourceDescriptor,
    ResourceIndexRecord,
    ResourceIndexUpsertRequest,
    ResourceRegistryQuery,
    ResourceRegistryQueryResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.resource_registry.redaction import redact_registry_payload


class ResourceRegistryService:
    """Maintain registry-owned descriptors without owning source records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ResourceRegistryService:
        return ResourceRegistryService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def upsert(self, request: ResourceIndexUpsertRequest) -> ResourceIndexRecord:
        """Upsert one safe resource descriptor into the registry index."""

        descriptor = _descriptor_with_context(request.descriptor, self._actor_context)
        authorize(
            self._policy_adapter,
            action_type="registry.resource.create",
            resource_type="resource",
            resource_id=descriptor.resource_uri,
            scope=descriptor.owner_scope,
            trace_id=descriptor.trace_id or self._actor_context.trace_id,
            actor_id=request.created_by or self._actor_context.actor_id,
            workspace_id=descriptor.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context={"registry_is_index_only": True},
        )
        record = ResourceIndexRecord(
            resource_index_id=request.resource_index_id or f"resource-index-{uuid4().hex}",
            descriptor=descriptor.model_copy(
                update={
                    "metadata": redact_registry_payload(
                        {
                            **descriptor.metadata,
                            "registry_source_of_truth": False,
                            "source_records_mutated": False,
                        }
                    ),
                    "last_seen_at": datetime.now(UTC),
                }
            ),
            created_at=datetime.now(UTC),
        )
        stored = _save_resource(self._repository, record)
        emit_telemetry(
            self._telemetry_service,
            event_type="resource_indexed",
            node_type="resource",
            node_id=stored.descriptor.resource_uri,
            intensity=0.7,
            trace_id=stored.descriptor.trace_id,
            payload={
                "resource_type": stored.descriptor.resource_type,
                "source_system": stored.descriptor.source_system,
            },
        )
        return stored

    def get_by_uri(self, resource_uri: str, scope: list[str]) -> ResourceIndexRecord | None:
        authorize(
            self._policy_adapter,
            action_type="registry.resource.read",
            resource_type="resource",
            resource_id=resource_uri,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_resource_by_uri", None)
        record = get(resource_uri) if callable(get) else None
        if not isinstance(record, ResourceIndexRecord):
            return None
        return record if _scope_matches(record.descriptor.owner_scope, scope) else None

    def get_by_type_id(
        self,
        resource_type: str,
        resource_id: str,
        scope: list[str],
    ) -> ResourceIndexRecord | None:
        authorize(
            self._policy_adapter,
            action_type="registry.resource.read",
            resource_type="resource",
            resource_id=f"{resource_type}:{resource_id}",
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_resource_by_type_id", None)
        record = get(resource_type, resource_id) if callable(get) else None
        if not isinstance(record, ResourceIndexRecord):
            return None
        return record if _scope_matches(record.descriptor.owner_scope, scope) else None

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
        list_resources = getattr(self._repository, "list_resources", None)
        if not callable(list_resources):
            return ResourceRegistryQueryResult(total_count=0)
        records = list_resources(query)
        resources = [record.descriptor for record in records]
        return ResourceRegistryQueryResult(
            resources=resources,
            total_count=len(resources),
            metadata={"registry_is_index_only": True},
        )

    def mark_deleted(self, resource_uri: str, scope: list[str], reason: str) -> ResourceIndexRecord:
        record = self.get_by_uri(resource_uri, scope)
        if record is None:
            raise ValueError("resource_not_found")
        authorize(
            self._policy_adapter,
            action_type="registry.resource.update",
            resource_type="resource",
            resource_id=resource_uri,
            scope=scope,
            trace_id=record.descriptor.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=record.descriptor.workspace_id,
            risk_level="medium",
            context={"reason": reason, "soft_delete_index_only": True},
        )
        descriptor = record.descriptor.model_copy(
            update={
                "status": "deleted",
                "deleted_at": datetime.now(UTC),
                "metadata": {**record.descriptor.metadata, "delete_reason": reason},
            }
        )
        return _save_resource(
            self._repository,
            record.model_copy(update={"descriptor": descriptor}),
        )


def _descriptor_with_context(
    descriptor: ResourceDescriptor,
    actor_context: ActorContext,
) -> ResourceDescriptor:
    return descriptor.model_copy(
        update={
            "trace_id": descriptor.trace_id or actor_context.trace_id,
            "actor_id": descriptor.actor_id or actor_context.actor_id,
            "workspace_id": descriptor.workspace_id or actor_context.workspace_id,
        }
    )


def _save_resource(repository: object, record: ResourceIndexRecord) -> ResourceIndexRecord:
    save = getattr(repository, "save_resource", None)
    stored = save(record) if callable(save) else record
    return stored if isinstance(stored, ResourceIndexRecord) else record


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["ResourceRegistryService"]
