"""Controlled registry rebuild orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.resource_references import (
    ResourceReferenceCreateRequest,
    ResourceReferenceLink,
)
from aion_brain.contracts.resource_registry import (
    RegistryRebuildRequest,
    RegistryRebuildRun,
    RegistryRunStatus,
    ResourceIndexUpsertRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class RegistryRebuilder:
    """Rebuild registry index records from configured local providers."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        scanner: object,
        registry_service: object,
        link_service: object,
        snapshot_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._scanner = scanner
        self._registry_service = registry_service
        self._link_service = link_service
        self._snapshot_service = snapshot_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RegistryRebuilder:
        return RegistryRebuilder(
            self._repository,
            self._policy_adapter,
            scanner=self._scanner,
            registry_service=self._registry_service,
            link_service=self._link_service,
            snapshot_service=self._snapshot_service,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def rebuild(self, request: RegistryRebuildRequest) -> RegistryRebuildRun:
        if self._settings is not None and not bool(
            getattr(self._settings, "registry_rebuild_enabled", True)
        ):
            raise RuntimeError("registry_rebuild_disabled")
        authorize(
            self._policy_adapter,
            action_type="registry.rebuild",
            resource_type="resource_registry",
            resource_id=request.rebuild_run_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context={"mode": request.mode, "clear_missing": request.clear_missing},
        )
        run_id = request.rebuild_run_id or f"registry-rebuild-{uuid4().hex}"
        trace_id = request.trace_id or self._actor_context.trace_id
        limit = int(getattr(self._settings, "registry_max_resources_per_rebuild", 5000))
        emit_telemetry(
            self._telemetry_service,
            event_type="registry_rebuild_started",
            node_type="registry_rebuild",
            node_id=run_id,
            intensity=0.8,
            trace_id=trace_id,
            payload={"mode": request.mode},
        )
        scan = getattr(self._scanner, "scan", None)
        descriptors = (
            scan(request.resource_types, request.source_systems, request.owner_scope, limit)
            if callable(scan)
            else []
        )
        links_indexed = 0
        failures: list[dict[str, object]] = []
        if request.mode == "controlled":
            for descriptor in descriptors:
                try:
                    cast(Any, self._registry_service).with_actor_context(
                        self._actor_context
                    ).upsert(
                        ResourceIndexUpsertRequest(
                            descriptor=descriptor,
                            created_by=request.created_by or self._actor_context.actor_id,
                        )
                    )
                    for link in _extract_links(self._scanner, descriptor):
                        if isinstance(link, ResourceReferenceLink):
                            cast(Any, self._link_service).with_actor_context(
                                self._actor_context
                            ).create_link(
                                ResourceReferenceCreateRequest(
                                    resource_link_id=link.resource_link_id,
                                    trace_id=link.trace_id,
                                    source_resource_uri=link.source_resource_uri,
                                    target_resource_uri=link.target_resource_uri,
                                    relation_type=link.relation_type,
                                    confidence=link.confidence,
                                    discovered_by=link.discovered_by,
                                    evidence_refs=link.evidence_refs,
                                    metadata=link.metadata,
                                    created_by=request.created_by or self._actor_context.actor_id,
                                ),
                                request.owner_scope,
                            )
                        links_indexed += 1
                except Exception as exc:
                    failures.append(
                        {
                            "resource_uri": descriptor.resource_uri,
                            "reason": exc.__class__.__name__,
                        }
                    )
        else:
            for descriptor in descriptors:
                links_indexed += len(_extract_links(self._scanner, descriptor))
        warnings = list(getattr(self._scanner, "warnings", []) or [])
        snapshot_id = None
        if (
            request.mode == "controlled"
            and request.create_snapshot
            and self._snapshot_service is not None
        ):
            try:
                snapshot = (
                    cast(Any, self._snapshot_service)
                    .with_actor_context(self._actor_context)
                    .create_snapshot(
                        request.owner_scope,
                        snapshot_type="rebuild",
                        trace_id=trace_id,
                        metadata={"rebuild_run_id": run_id},
                    )
                )
                snapshot_id = snapshot.registry_snapshot_id
            except Exception as exc:
                warnings.append({"reason": exc.__class__.__name__, "stage": "snapshot"})
        status = "dry_run" if request.mode == "dry_run" else "completed"
        if failures:
            status = "warning"
        now = datetime.now(UTC)
        run = RegistryRebuildRun(
            rebuild_run_id=run_id,
            trace_id=trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status=cast(RegistryRunStatus, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            resource_types=request.resource_types,
            source_systems=request.source_systems,
            resources_seen=len(descriptors),
            resources_indexed=0 if request.mode == "dry_run" else len(descriptors) - len(failures),
            links_indexed=links_indexed,
            skipped=0,
            failures=failures,
            warnings=warnings,
            result={
                "source_records_mutated": False,
                "snapshot_id": snapshot_id,
                "clear_missing_ignored_for_sources": bool(request.clear_missing),
            },
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            completed_at=now,
        )
        stored = _save_rebuild_run(self._repository, run)
        emit_telemetry(
            self._telemetry_service,
            event_type="registry_rebuild_completed",
            node_type="registry_rebuild",
            node_id=stored.rebuild_run_id,
            intensity=0.85 if stored.failures else 0.55,
            trace_id=stored.trace_id,
            payload={"resources_seen": stored.resources_seen, "failures": len(stored.failures)},
        )
        return stored

    def get_run(self, rebuild_run_id: str, scope: list[str]) -> RegistryRebuildRun | None:
        authorize(
            self._policy_adapter,
            action_type="registry.rebuild",
            resource_type="registry_rebuild_run",
            resource_id=rebuild_run_id,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_rebuild_run", None)
        run = get(rebuild_run_id) if callable(get) else None
        if not isinstance(run, RegistryRebuildRun):
            return None
        return run if set(run.owner_scope).intersection(scope) else None

    def list_runs(self, scope: list[str], limit: int = 100) -> list[RegistryRebuildRun]:
        authorize(
            self._policy_adapter,
            action_type="registry.rebuild",
            resource_type="registry_rebuild_run",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_runs = getattr(self._repository, "list_rebuild_runs", None)
        if not callable(list_runs):
            return []
        return [
            item
            for item in list_runs(limit=limit)
            if isinstance(item, RegistryRebuildRun) and set(item.owner_scope).intersection(scope)
        ]


def _extract_links(scanner: object, descriptor: object) -> list[object]:
    extract = getattr(scanner, "extract_links", None)
    return list(extract(descriptor) or []) if callable(extract) else []


def _save_rebuild_run(repository: object, run: RegistryRebuildRun) -> RegistryRebuildRun:
    save = getattr(repository, "save_rebuild_run", None)
    stored = save(run) if callable(save) else run
    return stored if isinstance(stored, RegistryRebuildRun) else run


__all__ = ["RegistryRebuilder"]
