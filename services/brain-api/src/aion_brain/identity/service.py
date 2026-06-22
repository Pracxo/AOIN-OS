"""Identity and workspace service."""

from datetime import UTC, datetime

from aion_brain.contracts.identity import (
    ActorRecord,
    PermissionGrant,
    WorkspaceMembership,
    WorkspaceRecord,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.identity.repository import IdentityRepository
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher


class IdentityPolicyDenied(Exception):
    """Raised when policy denies identity mutation or reads."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class IdentityService:
    """Policy-gated identity control plane service."""

    def __init__(
        self,
        *,
        repository: IdentityRepository | object,
        policy_adapter: PolicyAdapter,
        actor_context: ActorContext | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()
        self._telemetry_service = telemetry_service
        self._enricher = PolicyInputEnricher()

    def with_actor_context(self, actor_context: ActorContext) -> "IdentityService":
        """Return a service instance sharing dependencies with a new actor context."""
        return IdentityService(
            repository=self._repository,
            policy_adapter=self._policy_adapter,
            actor_context=actor_context,
            telemetry_service=self._telemetry_service,
        )

    def create_actor(self, record: ActorRecord) -> ActorRecord:
        """Create or update an actor."""
        self._ensure_allowed("identity.actor.create", "actor", record.actor_id, "medium")
        saved = _save_actor(self._repository, record)
        self._emit_identity_event(
            "actor_created",
            "actor",
            saved.actor_id,
            {"actor_type": saved.actor_type, "status": saved.status},
        )
        return saved

    def get_actor(self, actor_id: str) -> ActorRecord | None:
        """Return an actor by ID."""
        self._ensure_allowed("identity.actor.read", "actor", actor_id, "low")
        return _get_actor(self._repository, actor_id)

    def list_actors(self, status: str | None = None, limit: int = 50) -> list[ActorRecord]:
        """List actors."""
        self._ensure_allowed("identity.actor.read", "actor", None, "low")
        list_actors = getattr(self._repository, "list_actors", None)
        if callable(list_actors):
            result = list_actors(status=status, limit=limit)
            if isinstance(result, list):
                return [item for item in result if isinstance(item, ActorRecord)]
        return []

    def disable_actor(self, actor_id: str, reason: str | None = None) -> ActorRecord:
        """Disable an actor."""
        self._ensure_allowed("identity.actor.disable", "actor", actor_id, "medium")
        actor = _require(_get_actor(self._repository, actor_id), "actor_not_found")
        disabled = actor.model_copy(
            update={
                "status": "disabled",
                "disabled_at": datetime.now(UTC),
                "metadata": {**actor.metadata, "disable_reason": reason},
            }
        )
        saved = _save_actor(self._repository, disabled)
        self._emit_identity_event(
            "actor_disabled",
            "actor",
            saved.actor_id,
            {"status": saved.status, "reason": reason},
        )
        return saved

    def create_workspace(self, record: WorkspaceRecord) -> WorkspaceRecord:
        """Create or update a workspace."""
        self._ensure_allowed(
            "identity.workspace.create",
            "workspace",
            record.workspace_id,
            "medium",
        )
        saved = _save_workspace(self._repository, record)
        self._emit_identity_event(
            "workspace_created",
            "workspace",
            saved.workspace_id,
            {"status": saved.status, "owner_actor_id": saved.owner_actor_id},
        )
        return saved

    def get_workspace(self, workspace_id: str) -> WorkspaceRecord | None:
        """Return a workspace by ID."""
        self._ensure_allowed("identity.workspace.read", "workspace", workspace_id, "low")
        return _get_workspace(self._repository, workspace_id)

    def list_workspaces(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkspaceRecord]:
        """List workspaces."""
        self._ensure_allowed("identity.workspace.read", "workspace", None, "low")
        list_workspaces = getattr(self._repository, "list_workspaces", None)
        if callable(list_workspaces):
            result = list_workspaces(status=status, limit=limit)
            if isinstance(result, list):
                return [item for item in result if isinstance(item, WorkspaceRecord)]
        return []

    def archive_workspace(self, workspace_id: str, reason: str | None = None) -> WorkspaceRecord:
        """Archive a workspace."""
        self._ensure_allowed("identity.workspace.archive", "workspace", workspace_id, "medium")
        workspace = _require(_get_workspace(self._repository, workspace_id), "workspace_not_found")
        archived = workspace.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "metadata": {**workspace.metadata, "archive_reason": reason},
            }
        )
        saved = _save_workspace(self._repository, archived)
        self._emit_identity_event(
            "workspace_archived",
            "workspace",
            saved.workspace_id,
            {"status": saved.status, "reason": reason},
        )
        return saved

    def add_membership(self, record: WorkspaceMembership) -> WorkspaceMembership:
        """Add or update a workspace membership."""
        self._ensure_allowed(
            "identity.membership.create",
            "membership",
            record.membership_id,
            "medium",
        )
        saved = _save_membership(self._repository, record)
        self._emit_identity_event(
            "membership_created",
            "membership",
            saved.membership_id,
            {"workspace_id": saved.workspace_id, "actor_id": saved.actor_id, "role": saved.role},
        )
        return saved

    def get_membership(self, workspace_id: str, actor_id: str) -> WorkspaceMembership | None:
        """Return a membership by workspace and actor."""
        self._ensure_allowed("identity.membership.read", "membership", workspace_id, "low")
        get_membership = getattr(self._repository, "get_membership", None)
        if callable(get_membership):
            result = get_membership(workspace_id, actor_id)
            if result is None or isinstance(result, WorkspaceMembership):
                return result
        return None

    def list_memberships(
        self,
        workspace_id: str | None = None,
        actor_id: str | None = None,
    ) -> list[WorkspaceMembership]:
        """List memberships."""
        self._ensure_allowed("identity.membership.read", "membership", workspace_id, "low")
        list_memberships = getattr(self._repository, "list_memberships", None)
        if callable(list_memberships):
            result = list_memberships(workspace_id=workspace_id, actor_id=actor_id)
            if isinstance(result, list):
                return [item for item in result if isinstance(item, WorkspaceMembership)]
        return []

    def revoke_membership(
        self,
        membership_id: str,
        reason: str | None = None,
    ) -> WorkspaceMembership:
        """Revoke a membership."""
        self._ensure_allowed("identity.membership.revoke", "membership", membership_id, "medium")
        membership = _require(
            _get_membership_by_id(self._repository, membership_id),
            "membership_not_found",
        )
        revoked = membership.model_copy(
            update={
                "status": "revoked",
                "revoked_at": datetime.now(UTC),
                "metadata": {**membership.metadata, "revoke_reason": reason},
            }
        )
        saved = _save_membership(self._repository, revoked)
        self._emit_identity_event(
            "membership_revoked",
            "membership",
            saved.membership_id,
            {"workspace_id": saved.workspace_id, "actor_id": saved.actor_id, "reason": reason},
        )
        return saved

    def create_permission_grant(self, record: PermissionGrant) -> PermissionGrant:
        """Create or update a permission grant."""
        self._ensure_allowed(
            "identity.permission.create",
            "permission",
            record.grant_id,
            "medium",
        )
        saved = _save_permission_grant(self._repository, record)
        self._emit_identity_event(
            "permission_granted",
            "permission",
            saved.grant_id,
            {
                "permission": saved.permission,
                "resource_type": saved.resource_type,
                "effect": saved.effect,
            },
        )
        return saved

    def list_permission_grants(
        self,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        role: str | None = None,
    ) -> list[PermissionGrant]:
        """List permission grants."""
        self._ensure_allowed("identity.permission.read", "permission", None, "low")
        list_grants = getattr(self._repository, "list_permission_grants", None)
        if callable(list_grants):
            result = list_grants(actor_id=actor_id, workspace_id=workspace_id, role=role)
            if isinstance(result, list):
                return [item for item in result if isinstance(item, PermissionGrant)]
        return []

    def revoke_permission_grant(
        self,
        grant_id: str,
        reason: str | None = None,
    ) -> PermissionGrant:
        """Revoke a permission grant."""
        self._ensure_allowed("identity.permission.revoke", "permission", grant_id, "medium")
        grant = _require(_get_permission_grant(self._repository, grant_id), "grant_not_found")
        revoked = grant.model_copy(
            update={
                "status": "revoked",
                "revoked_at": datetime.now(UTC),
                "metadata": {**grant.metadata, "revoke_reason": reason},
            }
        )
        saved = _save_permission_grant(self._repository, revoked)
        self._emit_identity_event(
            "permission_revoked",
            "permission",
            saved.grant_id,
            {"permission": saved.permission, "reason": reason},
        )
        return saved

    def _ensure_allowed(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
    ) -> None:
        request = PolicyRequest(
            request_id=f"{action_type}-{resource_id or 'list'}",
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=False,
            requested_permissions=[],
            security_scope=self._actor_context.security_scope,
            context={},
        )
        decision = self._policy_adapter.authorize(
            self._enricher.enrich(request, self._actor_context)
        )
        if not decision.allow:
            raise IdentityPolicyDenied(decision)

    def _emit_identity_event(
        self,
        event_type: VisualTelemetryEventType,
        node_type: VisualNodeType,
        node_id: str,
        payload: dict[str, object],
    ) -> None:
        _emit(
            self._telemetry_service,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{node_id}-{event_type}",
                trace_id=(
                    self._actor_context.trace_id or self._actor_context.correlation_id or node_id
                ),
                event_type=event_type,
                node_type=node_type,
                node_id=node_id,
                edge_from=self._actor_context.actor_id,
                edge_to=node_id,
                intensity=0.6,
                payload=payload,
                created_at=datetime.now(UTC),
            ),
        )


def _require[T](value: T | None, reason: str) -> T:
    if value is None:
        raise ValueError(reason)
    return value


def _save_actor(repository: object, record: ActorRecord) -> ActorRecord:
    save = getattr(repository, "save_actor", None)
    if callable(save):
        result = save(record)
        if isinstance(result, ActorRecord):
            return result
    return record


def _get_actor(repository: object, actor_id: str) -> ActorRecord | None:
    get = getattr(repository, "get_actor", None)
    if callable(get):
        result = get(actor_id)
        if result is None or isinstance(result, ActorRecord):
            return result
    return None


def _save_workspace(repository: object, record: WorkspaceRecord) -> WorkspaceRecord:
    save = getattr(repository, "save_workspace", None)
    if callable(save):
        result = save(record)
        if isinstance(result, WorkspaceRecord):
            return result
    return record


def _get_workspace(repository: object, workspace_id: str) -> WorkspaceRecord | None:
    get = getattr(repository, "get_workspace", None)
    if callable(get):
        result = get(workspace_id)
        if result is None or isinstance(result, WorkspaceRecord):
            return result
    return None


def _save_membership(repository: object, record: WorkspaceMembership) -> WorkspaceMembership:
    save = getattr(repository, "save_membership", None)
    if callable(save):
        result = save(record)
        if isinstance(result, WorkspaceMembership):
            return result
    return record


def _get_membership_by_id(repository: object, membership_id: str) -> WorkspaceMembership | None:
    get = getattr(repository, "get_membership_by_id", None)
    if callable(get):
        result = get(membership_id)
        if result is None or isinstance(result, WorkspaceMembership):
            return result
    return None


def _save_permission_grant(repository: object, record: PermissionGrant) -> PermissionGrant:
    save = getattr(repository, "save_permission_grant", None)
    if callable(save):
        result = save(record)
        if isinstance(result, PermissionGrant):
            return result
    return record


def _get_permission_grant(repository: object, grant_id: str) -> PermissionGrant | None:
    get = getattr(repository, "get_permission_grant", None)
    if callable(get):
        result = get(grant_id)
        if result is None or isinstance(result, PermissionGrant):
            return result
    return None


def _emit(telemetry_service: object | None, event: VisualTelemetryEvent) -> None:
    if telemetry_service is None:
        return
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
        return
    save = getattr(telemetry_service, "save_visual_telemetry", None)
    if callable(save):
        save(event.trace_id, [event])
