"""Reference link and backlink services for the resource registry."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.resource_references import (
    ResourceReferenceCreateRequest,
    ResourceReferenceLink,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.resource_registry.uri import parse_resource_uri


class ResourceLinkService:
    """Create and inspect registry-owned resource reference links."""

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

    def with_actor_context(self, actor_context: ActorContext) -> ResourceLinkService:
        return ResourceLinkService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_link(
        self,
        request: ResourceReferenceCreateRequest,
        scope: list[str],
    ) -> ResourceReferenceLink:
        """Create a directed link without mutating either source record."""

        authorize(
            self._policy_adapter,
            action_type="registry.link.create",
            resource_type="resource_link",
            resource_id=request.resource_link_id,
            scope=scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
        )
        source = parse_resource_uri(request.source_resource_uri)
        target = parse_resource_uri(request.target_resource_uri)
        link = ResourceReferenceLink(
            resource_link_id=request.resource_link_id or f"resource-link-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            source_resource_uri=request.source_resource_uri,
            target_resource_uri=request.target_resource_uri,
            source_type=source["resource_type"],
            source_id=source["resource_id"],
            target_type=target["resource_type"],
            target_id=target["resource_id"],
            relation_type=request.relation_type,
            status="active",
            confidence=request.confidence,
            discovered_by=request.discovered_by,
            evidence_refs=request.evidence_refs,
            metadata={**request.metadata, "source_records_mutated": False},
            created_at=datetime.now(UTC),
        )
        stored = _save_link(self._repository, link)
        emit_telemetry(
            self._telemetry_service,
            event_type="resource_link_created",
            node_type="resource_link",
            node_id=stored.resource_link_id,
            intensity=0.65,
            trace_id=stored.trace_id,
            edge_from=stored.source_resource_uri,
            edge_to=stored.target_resource_uri,
            payload={
                "relation_type": stored.relation_type,
                "source_resource_uri": stored.source_resource_uri,
                "target_resource_uri": stored.target_resource_uri,
            },
        )
        return stored

    def list_links(
        self,
        scope: list[str],
        *,
        source_uri: str | None = None,
        target_uri: str | None = None,
        relation_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ResourceReferenceLink]:
        authorize(
            self._policy_adapter,
            action_type="registry.link.read",
            resource_type="resource_link",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_links = getattr(self._repository, "list_links", None)
        if not callable(list_links):
            return []
        return list(
            list_links(
                source_uri=source_uri,
                target_uri=target_uri,
                relation_type=relation_type,
                status=status,
                limit=limit,
            )
            or []
        )

    def mark_broken(self, resource_link_id: str, reason: str) -> ResourceReferenceLink:
        link = _require_link(self._repository, resource_link_id)
        authorize(
            self._policy_adapter,
            action_type="registry.link.update",
            resource_type="resource_link",
            resource_id=resource_link_id,
            scope=self._actor_context.security_scope or ["workspace:main"],
            trace_id=link.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        stored = _save_link(
            self._repository,
            link.model_copy(
                update={
                    "status": "broken",
                    "broken_at": datetime.now(UTC),
                    "metadata": {**link.metadata, "broken_reason": reason},
                }
            ),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="resource_link_broken",
            node_type="resource_link",
            node_id=stored.resource_link_id,
            intensity=0.9,
            trace_id=stored.trace_id,
            payload={"reason": reason},
        )
        return stored

    def soft_delete_link(self, resource_link_id: str, reason: str) -> ResourceReferenceLink:
        link = _require_link(self._repository, resource_link_id)
        authorize(
            self._policy_adapter,
            action_type="registry.link.delete",
            resource_type="resource_link",
            resource_id=resource_link_id,
            scope=self._actor_context.security_scope or ["workspace:main"],
            trace_id=link.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason, "soft_delete_only": True},
        )
        return _save_link(
            self._repository,
            link.model_copy(
                update={
                    "status": "deleted",
                    "deleted_at": datetime.now(UTC),
                    "metadata": {**link.metadata, "delete_reason": reason},
                }
            ),
        )


class BacklinkService:
    """Read and rebuild registry-owned backlink projections."""

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

    def with_actor_context(self, actor_context: ActorContext) -> BacklinkService:
        return BacklinkService(
            self._repository,
            self._policy_adapter,
            actor_context=actor_context,
        )

    def list_backlinks(
        self,
        resource_uri: str,
        scope: list[str],
        limit: int = 100,
    ) -> list[dict[str, object]]:
        authorize(
            self._policy_adapter,
            action_type="registry.backlink.read",
            resource_type="backlink",
            resource_id=resource_uri,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_backlinks = getattr(self._repository, "list_backlinks", None)
        if not callable(list_backlinks):
            return []
        return [dict(item) for item in list_backlinks(resource_uri, limit=limit) or []]

    def rebuild_backlinks(self, scope: list[str], *, dry_run: bool = True) -> dict[str, int]:
        authorize(
            self._policy_adapter,
            action_type="registry.link.update",
            resource_type="backlink",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"dry_run": dry_run},
        )
        list_links = getattr(self._repository, "list_links", None)
        save_backlink = getattr(self._repository, "save_backlink", None)
        if not callable(list_links):
            return {"links_seen": 0, "backlinks_written": 0}
        count = 0
        for link in list_links(limit=5000) or []:
            count += 1
            if not dry_run and callable(save_backlink) and link.status != "deleted":
                save_backlink(
                    {
                        "backlink_id": f"backlink-{link.resource_link_id}",
                        "resource_uri": link.target_resource_uri,
                        "referring_resource_uri": link.source_resource_uri,
                        "relation_type": link.relation_type,
                        "status": link.status,
                        "metadata": {"resource_link_id": link.resource_link_id},
                        "created_at": link.created_at or datetime.now(UTC),
                        "deleted_at": link.deleted_at,
                    }
                )
        return {"links_seen": count, "backlinks_written": 0 if dry_run else count}


def _save_link(repository: object, link: ResourceReferenceLink) -> ResourceReferenceLink:
    save = getattr(repository, "save_link", None)
    stored = save(link) if callable(save) else link
    return stored if isinstance(stored, ResourceReferenceLink) else link


def _require_link(repository: object, resource_link_id: str) -> ResourceReferenceLink:
    get = getattr(repository, "get_link", None)
    link = get(resource_link_id) if callable(get) else None
    if not isinstance(link, ResourceReferenceLink):
        raise ValueError("resource_link_not_found")
    return link


__all__ = ["BacklinkService", "ResourceLinkService"]
