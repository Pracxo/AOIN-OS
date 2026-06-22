"""Purge preview generation."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.lifecycle import PurgePreview
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class PurgePreviewService:
    """Generate purge previews without deleting source records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        registry_repository: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._registry_repository = registry_repository
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> PurgePreviewService:
        return PurgePreviewService(
            self._repository,
            self._policy_adapter,
            registry_repository=self._registry_repository,
            settings=self._settings,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_preview(
        self,
        resource_uris: list[str],
        scope: list[str],
        trace_id: str | None = None,
        created_by: str | None = None,
        *,
        persist: bool = True,
    ) -> PurgePreview:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.purge_preview.create",
            resource_type="purge_preview",
            resource_id=None,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"hard_delete_allowed": False, "purge_executed": False},
        )
        hard_delete_enabled = bool(getattr(self._settings, "lifecycle_hard_delete_enabled", False))
        blockers = []
        for uri in resource_uris:
            blockers.extend(_blockers_for_uri(uri, self._registry_repository, hard_delete_enabled))
        if not hard_delete_enabled:
            blockers.append(
                {
                    "blocker": "lifecycle_hard_delete_enabled=false",
                    "reason": "hard delete disabled in v0.1",
                }
            )
        preview = PurgePreview(
            purge_preview_id=f"purge-preview-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            status="blocked" if blockers else "created",
            owner_scope=scope,
            resource_uris=resource_uris,
            resource_count=len(resource_uris),
            blocked_count=len(resource_uris) if blockers else 0,
            allowed_count=0 if blockers else len(resource_uris),
            blockers=blockers,
            warnings=[],
            estimated_impact={
                "resources": len(resource_uris),
                "source_records_deleted": 0,
                "external_calls": False,
            },
            requires_backup=True,
            backup_verified=False,
            hard_delete_allowed=False,
            result={"purge_executed": False, "source_records_mutated": False},
            metadata={"preview_only": True},
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_preview(self._repository, preview) if persist else preview
        emit_telemetry(
            self._telemetry_service,
            event_type="purge_preview_created",
            node_type="purge_preview",
            node_id=stored.purge_preview_id,
            intensity=1.0 if stored.blocked_count > 0 else 0.6,
            trace_id=stored.trace_id,
            payload={
                "blocked_count": stored.blocked_count,
                "resource_count": stored.resource_count,
            },
        )
        return stored

    def get_preview(self, purge_preview_id: str, scope: list[str]) -> PurgePreview | None:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.purge_preview.read",
            resource_type="purge_preview",
            resource_id=purge_preview_id,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_purge_preview", None)
        preview = get(purge_preview_id) if callable(get) else None
        if not isinstance(preview, PurgePreview):
            return None
        return preview if set(preview.owner_scope).intersection(scope) else None

    def list_previews(
        self, scope: list[str], status: str | None = None, limit: int = 100
    ) -> list[PurgePreview]:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.purge_preview.read",
            resource_type="purge_preview",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_purge_previews", None)
        return list_items(scope, status=status, limit=limit) if callable(list_items) else []


def _blockers_for_uri(
    uri: str, registry_repository: object | None, hard_delete_enabled: bool
) -> list[dict[str, object]]:
    blockers: list[dict[str, object]] = []
    if not hard_delete_enabled:
        blockers.append({"resource_uri": uri, "blocker": "hard_delete_disabled"})
    get_resource = getattr(registry_repository, "get_resource_by_uri", None)
    resource = get_resource(uri) if callable(get_resource) else None
    resource_type = str(getattr(getattr(resource, "descriptor", None), "resource_type", ""))
    sensitivity = str(getattr(getattr(resource, "descriptor", None), "sensitivity", ""))
    if resource_type in {"audit_entry", "evidence", "evidence_chunk"}:
        blockers.append({"resource_uri": uri, "blocker": f"{resource_type}_retained"})
    if sensitivity == "restricted":
        blockers.append({"resource_uri": uri, "blocker": "resource_restricted"})
    list_links = getattr(registry_repository, "list_links", None)
    if callable(list_links):
        if list_links(source_uri=uri, limit=1) or list_links(target_uri=uri, limit=1):
            blockers.append({"resource_uri": uri, "blocker": "linked_resources_exist"})
    blockers.append({"resource_uri": uri, "blocker": "source_subsystem_does_not_support_purge"})
    blockers.append({"resource_uri": uri, "blocker": "backup_missing"})
    return blockers


def _save_preview(repository: object, preview: PurgePreview) -> PurgePreview:
    save = getattr(repository, "save_purge_preview", None)
    stored = save(preview) if callable(save) else preview
    return stored if isinstance(stored, PurgePreview) else preview


__all__ = ["PurgePreviewService"]
