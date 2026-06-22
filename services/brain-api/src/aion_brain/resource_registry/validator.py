"""Reference validation for the resource registry."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.incidents import IncidentSignalCreateRequest
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.contracts.resource_references import (
    BrokenReference,
    BrokenReferenceIssueType,
    OrphanedResource,
    ResourceReferenceLink,
)
from aion_brain.contracts.resource_registry import (
    ReferenceValidationRequest,
    ReferenceValidationRun,
    RegistryRunStatus,
    ResourceIndexRecord,
    ResourceRegistryQuery,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.resource_registry.uri import parse_resource_uri, validate_resource_uri


class ReferenceValidator:
    """Validate registry links without mutating source systems."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        notification_router: object | None = None,
        incident_signal_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._notification_router = notification_router
        self._incident_signal_service = incident_signal_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ReferenceValidator:
        return ReferenceValidator(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            notification_router=self._notification_router,
            incident_signal_service=self._incident_signal_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def validate(self, request: ReferenceValidationRequest) -> ReferenceValidationRun:
        if self._settings is not None and not bool(
            getattr(self._settings, "resource_reference_validation_enabled", True)
        ):
            raise RuntimeError("resource_reference_validation_disabled")
        authorize(
            self._policy_adapter,
            action_type="registry.validate",
            resource_type="resource_registry",
            resource_id=request.validation_run_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context={"mode": request.mode},
        )
        run_id = request.validation_run_id or f"reference-validation-{uuid4().hex}"
        trace_id = request.trace_id or self._actor_context.trace_id
        emit_telemetry(
            self._telemetry_service,
            event_type="reference_validation_started",
            node_type="registry_validation",
            node_id=run_id,
            intensity=0.75,
            trace_id=trace_id,
            payload={"mode": request.mode},
        )
        resources = _load_resources(self._repository, request)
        resource_by_uri = {item.descriptor.resource_uri: item for item in resources}
        links = _load_links(self._repository)
        broken = _find_broken_links(links, resource_by_uri, request, run_id)
        orphans = (
            _find_orphans(resources, links, request, run_id) if request.include_orphans else []
        )
        status = "dry_run" if request.mode == "dry_run" else "completed"
        if broken or orphans:
            status = "warning" if request.mode == "controlled" else "dry_run"
        now = datetime.now(UTC)
        run = ReferenceValidationRun(
            validation_run_id=run_id,
            trace_id=trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status=cast(RegistryRunStatus, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            resource_types=request.resource_types,
            source_systems=request.source_systems,
            resources_checked=len(resources),
            links_checked=len(links),
            broken_count=len(broken),
            orphaned_count=len(orphans),
            stale_count=sum(1 for item in broken if item.issue_type == "stale_target"),
            broken_references=broken,
            orphaned_resources=orphans,
            warnings=[],
            failures=[],
            result={"source_records_mutated": False, "repair_attempted": False},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            completed_at=now,
        )
        if request.mode == "controlled":
            for item in broken:
                _save_broken(self._repository, item)
                emit_telemetry(
                    self._telemetry_service,
                    event_type="broken_reference_detected",
                    node_type="broken_reference",
                    node_id=item.broken_reference_id,
                    intensity=0.9,
                    trace_id=item.trace_id,
                    payload={"issue_type": item.issue_type, "severity": item.severity},
                )
            for orphan_item in orphans:
                _save_orphan(self._repository, orphan_item)
                emit_telemetry(
                    self._telemetry_service,
                    event_type="orphaned_resource_detected",
                    node_type="orphaned_resource",
                    node_id=orphan_item.orphaned_resource_id,
                    intensity=0.7,
                    trace_id=orphan_item.trace_id,
                    payload={
                        "issue_type": orphan_item.issue_type,
                        "severity": orphan_item.severity,
                    },
                )
        _save_validation_run(self._repository, run)
        self._maybe_notify(request, run)
        self._maybe_create_incident(request, run)
        emit_telemetry(
            self._telemetry_service,
            event_type="reference_validation_completed",
            node_type="registry_validation",
            node_id=run.validation_run_id,
            intensity=0.8 if broken or orphans else 0.5,
            trace_id=run.trace_id,
            payload={"broken_count": run.broken_count, "orphaned_count": run.orphaned_count},
        )
        return run

    def get_run(self, validation_run_id: str, scope: list[str]) -> ReferenceValidationRun | None:
        authorize(
            self._policy_adapter,
            action_type="registry.validate",
            resource_type="reference_validation_run",
            resource_id=validation_run_id,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_validation_run", None)
        run = get(validation_run_id) if callable(get) else None
        if not isinstance(run, ReferenceValidationRun):
            return None
        return run if set(run.owner_scope).intersection(scope) else None

    def list_broken_references(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        validation_run_id: str | None = None,
        limit: int = 100,
    ) -> list[BrokenReference]:
        authorize(
            self._policy_adapter,
            action_type="registry.broken_reference.read",
            resource_type="broken_reference",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_broken_references", None)
        if not callable(list_items):
            return []
        return list(
            list_items(
                status=status,
                severity=severity,
                validation_run_id=validation_run_id,
                limit=limit,
            )
            or []
        )

    def dismiss_broken_reference(
        self,
        broken_reference_id: str,
        scope: list[str],
        reason: str,
    ) -> BrokenReference:
        item = _require_broken(self._repository, broken_reference_id)
        authorize(
            self._policy_adapter,
            action_type="registry.broken_reference.update",
            resource_type="broken_reference",
            resource_id=broken_reference_id,
            scope=scope,
            trace_id=item.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return _save_broken(
            self._repository,
            item.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {**item.metadata, "dismiss_reason": reason},
                }
            ),
        )

    def list_orphaned_resources(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        validation_run_id: str | None = None,
        limit: int = 100,
    ) -> list[OrphanedResource]:
        authorize(
            self._policy_adapter,
            action_type="registry.orphaned_resource.read",
            resource_type="orphaned_resource",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_orphaned_resources", None)
        if not callable(list_items):
            return []
        return list(
            list_items(
                status=status,
                severity=severity,
                validation_run_id=validation_run_id,
                limit=limit,
            )
            or []
        )

    def dismiss_orphaned_resource(
        self,
        orphaned_resource_id: str,
        scope: list[str],
        reason: str,
    ) -> OrphanedResource:
        item = _require_orphan(self._repository, orphaned_resource_id)
        authorize(
            self._policy_adapter,
            action_type="registry.orphaned_resource.update",
            resource_type="orphaned_resource",
            resource_id=orphaned_resource_id,
            scope=scope,
            trace_id=item.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return _save_orphan(
            self._repository,
            item.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {**item.metadata, "dismiss_reason": reason},
                }
            ),
        )

    def _maybe_notify(
        self,
        request: ReferenceValidationRequest,
        run: ReferenceValidationRun,
    ) -> None:
        should_notify = request.create_notifications or bool(
            getattr(self._settings, "registry_create_notifications_default", False)
        )
        if not should_notify or run.broken_count + run.orphaned_count == 0:
            return
        publish = getattr(self._notification_router, "publish", None)
        if not callable(publish):
            return
        try:
            publish(
                NotificationPublishRequest(
                    topic_key="registry.validation",
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    severity="medium",
                    title="Registry validation requires attention",
                    message="AION detected broken or orphaned registry references.",
                    source_type="generic",
                    source_id=run.validation_run_id,
                    target_type="operator",
                    target_id="registry",
                    owner_scope=run.owner_scope,
                    refs=[run.validation_run_id],
                    metadata={
                        "broken_count": run.broken_count,
                        "orphaned_count": run.orphaned_count,
                    },
                    created_by=run.created_by,
                )
            )
        except Exception:
            return

    def _maybe_create_incident(
        self,
        request: ReferenceValidationRequest,
        run: ReferenceValidationRun,
    ) -> None:
        should_signal = request.create_incident_signals or bool(
            getattr(self._settings, "registry_create_incident_signals_default", False)
        )
        if not should_signal or run.broken_count + run.orphaned_count == 0:
            return
        create_signal = getattr(self._incident_signal_service, "create_signal", None)
        if not callable(create_signal):
            return
        try:
            create_signal(
                IncidentSignalCreateRequest(
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    source_type="generic",
                    source_id=run.validation_run_id,
                    signal_type="degraded",
                    severity="medium",
                    title="Registry link integrity degraded",
                    summary="AION detected broken or orphaned registry references.",
                    owner_scope=run.owner_scope,
                    refs=[run.validation_run_id],
                    metadata={
                        "broken_count": run.broken_count,
                        "orphaned_count": run.orphaned_count,
                    },
                    created_by=run.created_by,
                )
            )
        except Exception:
            return


def _load_resources(
    repository: object,
    request: ReferenceValidationRequest,
) -> list[ResourceIndexRecord]:
    list_resources = getattr(repository, "list_resources", None)
    if not callable(list_resources):
        return []
    query = ResourceRegistryQuery(
        scope=request.owner_scope,
        resource_type=request.resource_types[0] if len(request.resource_types) == 1 else None,
        source_system=request.source_systems[0] if len(request.source_systems) == 1 else None,
        include_deleted=True,
        limit=1000,
    )
    records = list(list_resources(query) or [])
    if request.resource_types:
        allowed_types = set(request.resource_types)
        records = [item for item in records if item.descriptor.resource_type in allowed_types]
    if request.source_systems:
        allowed_sources = set(request.source_systems)
        records = [item for item in records if item.descriptor.source_system in allowed_sources]
    return records


def _load_links(repository: object) -> list[ResourceReferenceLink]:
    list_links = getattr(repository, "list_links", None)
    if not callable(list_links):
        return []
    return list(list_links(limit=5000) or [])


def _find_broken_links(
    links: list[ResourceReferenceLink],
    resources: dict[str, ResourceIndexRecord],
    request: ReferenceValidationRequest,
    run_id: str,
) -> list[BrokenReference]:
    broken: list[BrokenReference] = []
    for link in links:
        issue_type: str | None = None
        reason: str | None = None
        if not validate_resource_uri(link.source_resource_uri) or not validate_resource_uri(
            link.target_resource_uri
        ):
            issue_type = "invalid_uri"
            reason = "Link contains an invalid AION resource URI."
        elif link.source_resource_uri not in resources:
            issue_type = "missing_source"
            reason = "Source resource is not indexed."
        elif link.target_resource_uri not in resources:
            issue_type = "missing_target"
            reason = "Target resource is not indexed."
        else:
            source = resources[link.source_resource_uri].descriptor
            target = resources[link.target_resource_uri].descriptor
            if target.status == "deleted" or target.deleted_at is not None:
                issue_type = "deleted_target"
                reason = "Target resource index is marked deleted."
            elif target.status == "stale" and request.include_stale:
                issue_type = "stale_target"
                reason = "Target resource index is marked stale."
            elif (
                source.owner_scope
                and target.owner_scope
                and not set(source.owner_scope).intersection(target.owner_scope)
            ):
                issue_type = "scope_mismatch"
                reason = "Source and target resource scopes do not overlap."
        if issue_type and reason:
            parsed_target = _safe_parse(link.target_resource_uri, link.target_type, link.target_id)
            parsed_source = _safe_parse(link.source_resource_uri, link.source_type, link.source_id)
            broken.append(
                BrokenReference(
                    broken_reference_id=f"broken-reference-{uuid4().hex}",
                    trace_id=link.trace_id,
                    source_resource_uri=link.source_resource_uri,
                    target_resource_uri=link.target_resource_uri,
                    source_type=parsed_source["resource_type"],
                    source_id=parsed_source["resource_id"],
                    target_type=parsed_target["resource_type"],
                    target_id=parsed_target["resource_id"],
                    issue_type=cast(BrokenReferenceIssueType, issue_type),
                    severity="medium" if issue_type != "invalid_uri" else "high",
                    status="open",
                    reason=reason,
                    recommended_action=(
                        "Review the registry link and update the owning source system if needed."
                    ),
                    validation_run_id=run_id,
                    metadata={
                        "resource_link_id": link.resource_link_id,
                        "source_records_mutated": False,
                    },
                    created_at=datetime.now(UTC),
                )
            )
    return broken


def _find_orphans(
    resources: list[ResourceIndexRecord],
    links: list[ResourceReferenceLink],
    request: ReferenceValidationRequest,
    run_id: str,
) -> list[OrphanedResource]:
    inbound = Counter(link.target_resource_uri for link in links if link.status != "deleted")
    outbound = Counter(link.source_resource_uri for link in links if link.status != "deleted")
    orphans: list[OrphanedResource] = []
    for record in resources:
        descriptor = record.descriptor
        if not set(descriptor.owner_scope).intersection(request.owner_scope):
            continue
        inbound_count = inbound[descriptor.resource_uri]
        outbound_count = outbound[descriptor.resource_uri]
        if inbound_count or outbound_count:
            continue
        orphans.append(
            OrphanedResource(
                orphaned_resource_id=f"orphaned-resource-{uuid4().hex}",
                trace_id=descriptor.trace_id,
                resource_uri=descriptor.resource_uri,
                resource_type=descriptor.resource_type,
                resource_id=descriptor.resource_id,
                source_system=descriptor.source_system,
                issue_type="no_inbound_refs",
                severity="low",
                status="open",
                reason="Resource has no active inbound or outbound registry references.",
                inbound_ref_count=inbound_count,
                outbound_ref_count=outbound_count,
                validation_run_id=run_id,
                metadata={"source_records_mutated": False},
                created_at=datetime.now(UTC),
            )
        )
    return orphans


def _safe_parse(resource_uri: str, fallback_type: str, fallback_id: str) -> dict[str, str]:
    try:
        return parse_resource_uri(resource_uri)
    except Exception:
        return {"resource_type": fallback_type, "resource_id": fallback_id}


def _save_validation_run(repository: object, run: ReferenceValidationRun) -> ReferenceValidationRun:
    save = getattr(repository, "save_validation_run", None)
    stored = save(run) if callable(save) else run
    return stored if isinstance(stored, ReferenceValidationRun) else run


def _save_broken(repository: object, item: BrokenReference) -> BrokenReference:
    save = getattr(repository, "save_broken_reference", None)
    stored = save(item) if callable(save) else item
    return stored if isinstance(stored, BrokenReference) else item


def _save_orphan(repository: object, item: OrphanedResource) -> OrphanedResource:
    save = getattr(repository, "save_orphaned_resource", None)
    stored = save(item) if callable(save) else item
    return stored if isinstance(stored, OrphanedResource) else item


def _require_broken(repository: object, broken_reference_id: str) -> BrokenReference:
    get = getattr(repository, "get_broken_reference", None)
    item = get(broken_reference_id) if callable(get) else None
    if not isinstance(item, BrokenReference):
        raise ValueError("broken_reference_not_found")
    return item


def _require_orphan(repository: object, orphaned_resource_id: str) -> OrphanedResource:
    get = getattr(repository, "get_orphaned_resource", None)
    item = get(orphaned_resource_id) if callable(get) else None
    if not isinstance(item, OrphanedResource):
        raise ValueError("orphaned_resource_not_found")
    return item


__all__ = ["ReferenceValidator"]
