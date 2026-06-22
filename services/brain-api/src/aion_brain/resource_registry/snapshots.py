"""Deterministic registry snapshots."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.resource_registry import RegistrySnapshot, RegistrySnapshotType
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class RegistrySnapshotService:
    """Create and read registry-owned integrity snapshots."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RegistrySnapshotService:
        return RegistrySnapshotService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_snapshot(
        self,
        scope: list[str],
        *,
        snapshot_type: RegistrySnapshotType = "manual",
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RegistrySnapshot:
        if self._settings is not None and not bool(
            getattr(self._settings, "registry_snapshots_enabled", True)
        ):
            raise RuntimeError("registry_snapshots_disabled")
        authorize(
            self._policy_adapter,
            action_type="registry.snapshot.create",
            resource_type="registry_snapshot",
            resource_id=None,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"snapshot_type": snapshot_type},
        )
        resources = _list_resources(self._repository, scope)
        links = _list_links(self._repository)
        broken = _list_broken(self._repository)
        orphans = _list_orphans(self._repository)
        resource_type_counts = Counter(item.descriptor.resource_type for item in resources)
        source_system_counts = Counter(item.descriptor.source_system for item in resources)
        report = {
            "resources": [item.descriptor.model_dump(mode="json") for item in resources],
            "links": [item.model_dump(mode="json") for item in links],
            "broken_references": [item.model_dump(mode="json") for item in broken],
            "orphaned_resources": [item.model_dump(mode="json") for item in orphans],
            "source_records_mutated": False,
        }
        snapshot = RegistrySnapshot(
            registry_snapshot_id=f"registry-snapshot-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            status="active",
            snapshot_type=snapshot_type,
            owner_scope=scope,
            resource_count=len(resources),
            link_count=len(links),
            broken_count=len(broken),
            orphaned_count=len(orphans),
            resource_type_counts=dict(resource_type_counts),
            source_system_counts=dict(source_system_counts),
            root_hash=_stable_hash(report),
            report=report,
            metadata={**(metadata or {}), "registry_source_of_truth": False},
            created_by=self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_snapshot(self._repository, snapshot)
        emit_telemetry(
            self._telemetry_service,
            event_type="registry_snapshot_created",
            node_type="registry_snapshot",
            node_id=stored.registry_snapshot_id,
            intensity=0.65,
            trace_id=stored.trace_id,
            payload={"snapshot_type": stored.snapshot_type, "root_hash": stored.root_hash},
        )
        return stored

    def get_snapshot(self, registry_snapshot_id: str, scope: list[str]) -> RegistrySnapshot | None:
        authorize(
            self._policy_adapter,
            action_type="registry.snapshot.read",
            resource_type="registry_snapshot",
            resource_id=registry_snapshot_id,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_snapshot", None)
        snapshot = get(registry_snapshot_id) if callable(get) else None
        if not isinstance(snapshot, RegistrySnapshot):
            return None
        return snapshot if set(snapshot.owner_scope).intersection(scope) else None

    def list_snapshots(
        self,
        scope: list[str],
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[RegistrySnapshot]:
        authorize(
            self._policy_adapter,
            action_type="registry.snapshot.read",
            resource_type="registry_snapshot",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_snapshots = getattr(self._repository, "list_snapshots", None)
        if not callable(list_snapshots):
            return []
        return [
            item
            for item in list_snapshots(snapshot_type=snapshot_type, status=status, limit=limit)
            if set(item.owner_scope).intersection(scope)
        ]


def _stable_hash(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _list_resources(repository: object, scope: list[str]) -> list[Any]:
    from aion_brain.contracts.resource_registry import ResourceRegistryQuery

    list_resources = getattr(repository, "list_resources", None)
    if not callable(list_resources):
        return []
    return list(
        list_resources(ResourceRegistryQuery(scope=scope, include_deleted=True, limit=1000)) or []
    )


def _list_links(repository: object) -> list[Any]:
    list_links = getattr(repository, "list_links", None)
    return list(list_links(limit=5000) or []) if callable(list_links) else []


def _list_broken(repository: object) -> list[Any]:
    list_broken = getattr(repository, "list_broken_references", None)
    return list(list_broken(limit=5000) or []) if callable(list_broken) else []


def _list_orphans(repository: object) -> list[Any]:
    list_orphans = getattr(repository, "list_orphaned_resources", None)
    return list(list_orphans(limit=5000) or []) if callable(list_orphans) else []


def _save_snapshot(repository: object, snapshot: RegistrySnapshot) -> RegistrySnapshot:
    save = getattr(repository, "save_snapshot", None)
    stored = save(snapshot) if callable(save) else snapshot
    return stored if isinstance(stored, RegistrySnapshot) else snapshot


__all__ = ["RegistrySnapshotService"]
