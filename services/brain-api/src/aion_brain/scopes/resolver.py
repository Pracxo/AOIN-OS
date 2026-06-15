"""Deterministic scope resolver."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.identity import (
    ActorRecord,
    PermissionGrant,
    WorkspaceMembership,
    WorkspaceRecord,
)
from aion_brain.contracts.scopes import ActorContext, ScopeResolution, ScopeResolutionRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent

READ_ACTIONS_ALLOWED_FOR_ARCHIVED_WORKSPACE = {"trace.read", "policy.authorize"}


class ScopeResolver:
    """Resolve scopes and permissions for an actor action."""

    def __init__(
        self,
        *,
        identity_repository: object,
        scope_repository: object,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._identity_repository = identity_repository
        self._scope_repository = scope_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def resolve(
        self,
        request: ScopeResolutionRequest,
        actor_context: ActorContext,
    ) -> ScopeResolution:
        """Resolve requested scopes against actor context and grants."""
        actor_id = request.actor_id or actor_context.actor_id
        workspace_id = request.workspace_id or actor_context.workspace_id
        constraints: list[str] = []
        resolved_scopes = set(actor_context.security_scope)
        permissions = set(actor_context.permissions)
        roles = set(actor_context.roles)

        actor = _get_actor(self._identity_repository, actor_id)
        if actor is not None and actor.status == "disabled":
            constraints.append("actor_disabled")

        if actor_id:
            resolved_scopes.add(f"actor:{actor_id}")
        membership = _membership(self._identity_repository, workspace_id, actor_id)
        if membership is not None and membership.status == "active":
            roles.add(membership.role)
            resolved_scopes.add(f"workspace:{membership.workspace_id}")
        elif workspace_id and actor_context.dev_mode and "owner" in actor_context.roles:
            resolved_scopes.add(f"workspace:{workspace_id}")
        elif workspace_id:
            constraints.append("workspace_membership_required")

        workspace = _get_workspace(self._identity_repository, workspace_id)
        if (
            workspace is not None
            and workspace.status == "archived"
            and not (
                actor_context.dev_mode
                and request.action_type in READ_ACTIONS_ALLOWED_FOR_ARCHIVED_WORKSPACE
            )
        ):
            constraints.append("workspace_archived")

        grants = _active_grants(self._identity_repository, actor_id, workspace_id, roles)
        denied_permissions = {
            grant.permission
            for grant in grants
            if grant.effect == "deny" and _grant_matches(grant, request)
        }
        allowed_permissions = {
            grant.permission
            for grant in grants
            if grant.effect == "allow" and _grant_matches(grant, request)
        }
        permissions.update(allowed_permissions)
        permissions.difference_update(denied_permissions)

        required_permissions = _required_permissions(request.action_type)
        has_required_permission = bool(permissions.intersection(required_permissions))
        dev_owner = actor_context.dev_mode and "owner" in roles
        requested_scopes = set(request.requested_scopes)
        scopes_within_resolution = requested_scopes.issubset(resolved_scopes)
        if not scopes_within_resolution:
            constraints.append("requested_scope_outside_actor_context")
        if denied_permissions.intersection(required_permissions):
            constraints.append("permission_denied_by_grant")
        if not has_required_permission and not dev_owner:
            constraints.append("required_permission_missing")

        allow = not constraints and (has_required_permission or dev_owner)
        resolution = ScopeResolution(
            scope_resolution_id=f"scope-resolution-{uuid4().hex}",
            actor_id=actor_id,
            workspace_id=workspace_id,
            requested_scopes=list(request.requested_scopes),
            resolved_scopes=sorted(resolved_scopes),
            permissions=sorted(permissions),
            allow=allow,
            constraints=constraints,
            created_at=datetime.now(UTC),
        )
        _save_resolution(self._scope_repository, resolution)
        _emit(self._telemetry_service, resolution)
        return resolution


def _get_actor(repository: object, actor_id: str | None) -> ActorRecord | None:
    if actor_id is None:
        return None
    get = getattr(repository, "get_actor", None)
    if callable(get):
        result = get(actor_id)
        if result is None or isinstance(result, ActorRecord):
            return result
    return None


def _get_workspace(repository: object, workspace_id: str | None) -> WorkspaceRecord | None:
    if workspace_id is None:
        return None
    get = getattr(repository, "get_workspace", None)
    if callable(get):
        result = get(workspace_id)
        if result is None or isinstance(result, WorkspaceRecord):
            return result
    return None


def _membership(
    repository: object,
    workspace_id: str | None,
    actor_id: str | None,
) -> WorkspaceMembership | None:
    if workspace_id is None or actor_id is None:
        return None
    get = getattr(repository, "get_membership", None)
    if callable(get):
        result = get(workspace_id, actor_id)
        if result is None or isinstance(result, WorkspaceMembership):
            return result
    return None


def _active_grants(
    repository: object,
    actor_id: str | None,
    workspace_id: str | None,
    roles: set[str],
) -> list[PermissionGrant]:
    grants: list[PermissionGrant] = []
    list_grants = getattr(repository, "list_permission_grants", None)
    if not callable(list_grants):
        return []
    for target, kwargs in (
        (actor_id, {"actor_id": actor_id, "workspace_id": None, "role": None}),
        (workspace_id, {"actor_id": None, "workspace_id": workspace_id, "role": None}),
    ):
        if target is None:
            continue
        result = list_grants(**kwargs)
        if isinstance(result, list):
            grants.extend(item for item in result if isinstance(item, PermissionGrant))
    for role in roles:
        result = list_grants(actor_id=None, workspace_id=None, role=role)
        if isinstance(result, list):
            grants.extend(item for item in result if isinstance(item, PermissionGrant))
    now = datetime.now(UTC)
    return [
        grant
        for grant in grants
        if grant.status == "active" and (grant.expires_at is None or grant.expires_at > now)
    ]


def _grant_matches(grant: PermissionGrant, request: ScopeResolutionRequest) -> bool:
    if grant.resource_type != request.resource_type:
        return False
    if grant.resource_id is not None and grant.resource_id != request.resource_id:
        return False
    return grant.permission in _required_permissions(request.action_type)


def _required_permissions(action_type: str) -> set[str]:
    mapped = {
        "memory.retrieve": "memory.read",
        "memory.write": "memory.write",
        "graph.retrieve": "graph.read",
        "graph.write": "graph.write",
        "capability.list": "capability.read",
        "trace.read": "trace.read",
        "policy.authorize": "policy.authorize",
        "scope.resolve": "scope.resolve",
    }
    return {action_type, mapped.get(action_type, action_type)}


def _save_resolution(repository: object, resolution: ScopeResolution) -> None:
    save = getattr(repository, "save", None)
    if callable(save):
        save(resolution)


def _emit(telemetry_service: object | None, resolution: ScopeResolution) -> None:
    if telemetry_service is None:
        return
    event = VisualTelemetryEvent(
        telemetry_id=f"telemetry-{resolution.scope_resolution_id}",
        trace_id=resolution.scope_resolution_id,
        event_type="scope_resolved",
        node_type="scope",
        node_id=resolution.scope_resolution_id,
        edge_from=resolution.actor_id,
        edge_to=resolution.workspace_id,
        intensity=0.7 if resolution.allow else 0.3,
        payload={"allow": resolution.allow, "constraints": resolution.constraints},
        created_at=datetime.now(UTC),
    )
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
        return
    save = getattr(telemetry_service, "save_visual_telemetry", None)
    if callable(save):
        save(resolution.scope_resolution_id, [event])
