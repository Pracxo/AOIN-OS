"""Identity service tests."""

from aion_brain.contracts.identity import (
    ActorRecord,
    PermissionGrant,
    WorkspaceMembership,
    WorkspaceRecord,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.identity.service import IdentityService
from tests.test_identity_contracts import make_actor, make_grant, make_membership, make_workspace


class FakePolicyAdapter:
    """Policy fake."""

    def __init__(self, *, deny: bool = False) -> None:
        self.deny = deny
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=not self.deny,
            approval_required=False,
            reason="allowed" if not self.deny else "denied",
            constraints=[] if not self.deny else ["blocked"],
            audit_level="standard",
        )


class FakeIdentityRepository:
    """In-memory identity repository fake."""

    def __init__(self) -> None:
        self.actors: dict[str, ActorRecord] = {}
        self.workspaces: dict[str, WorkspaceRecord] = {}
        self.memberships: dict[str, WorkspaceMembership] = {}
        self.grants: dict[str, PermissionGrant] = {}

    def save_actor(self, actor: ActorRecord) -> ActorRecord:
        self.actors[actor.actor_id] = actor
        return actor

    def get_actor(self, actor_id: str) -> ActorRecord | None:
        return self.actors.get(actor_id)

    def list_actors(self, *, status: str | None = None, limit: int = 50) -> list[ActorRecord]:
        matching_actors = [
            actor for actor in self.actors.values() if status is None or actor.status == status
        ]
        return matching_actors[:limit]

    def save_workspace(self, workspace: WorkspaceRecord) -> WorkspaceRecord:
        self.workspaces[workspace.workspace_id] = workspace
        return workspace

    def get_workspace(self, workspace_id: str) -> WorkspaceRecord | None:
        return self.workspaces.get(workspace_id)

    def list_workspaces(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkspaceRecord]:
        return [
            workspace
            for workspace in self.workspaces.values()
            if status is None or workspace.status == status
        ][:limit]

    def save_membership(self, membership: WorkspaceMembership) -> WorkspaceMembership:
        self.memberships[membership.membership_id] = membership
        return membership

    def get_membership(self, workspace_id: str, actor_id: str) -> WorkspaceMembership | None:
        for membership in self.memberships.values():
            if membership.workspace_id == workspace_id and membership.actor_id == actor_id:
                return membership
        return None

    def get_membership_by_id(self, membership_id: str) -> WorkspaceMembership | None:
        return self.memberships.get(membership_id)

    def list_memberships(
        self,
        *,
        workspace_id: str | None = None,
        actor_id: str | None = None,
    ) -> list[WorkspaceMembership]:
        return [
            membership
            for membership in self.memberships.values()
            if (workspace_id is None or membership.workspace_id == workspace_id)
            and (actor_id is None or membership.actor_id == actor_id)
        ]

    def save_permission_grant(self, grant: PermissionGrant) -> PermissionGrant:
        self.grants[grant.grant_id] = grant
        return grant

    def get_permission_grant(self, grant_id: str) -> PermissionGrant | None:
        return self.grants.get(grant_id)

    def list_permission_grants(
        self,
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        role: str | None = None,
    ) -> list[PermissionGrant]:
        return [
            grant
            for grant in self.grants.values()
            if (actor_id is None or grant.actor_id == actor_id)
            and (workspace_id is None or grant.workspace_id == workspace_id)
            and (role is None or grant.role == role)
        ]


class FakeTelemetry:
    """Visual telemetry fake."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_identity_service_creates_and_disables_actor() -> None:
    """IdentityService manages actor lifecycle."""
    repository = FakeIdentityRepository()
    service = make_service(repository)

    actor = service.create_actor(make_actor())
    disabled = service.disable_actor(actor.actor_id, "test")

    assert repository.actors[actor.actor_id].status == "disabled"
    assert disabled.disabled_at is not None


def test_identity_service_creates_and_archives_workspace() -> None:
    """IdentityService manages workspace lifecycle."""
    repository = FakeIdentityRepository()
    service = make_service(repository)

    workspace = service.create_workspace(make_workspace())
    archived = service.archive_workspace(workspace.workspace_id, "done")

    assert archived.status == "archived"
    assert archived.archived_at is not None


def test_identity_service_creates_and_revokes_membership() -> None:
    """IdentityService manages membership lifecycle."""
    repository = FakeIdentityRepository()
    service = make_service(repository)

    membership = service.add_membership(make_membership())
    revoked = service.revoke_membership(membership.membership_id, "done")

    assert revoked.status == "revoked"
    assert revoked.revoked_at is not None


def test_identity_service_creates_and_revokes_permission_grant() -> None:
    """IdentityService manages permission grant lifecycle."""
    repository = FakeIdentityRepository()
    service = make_service(repository)

    grant = service.create_permission_grant(make_grant())
    revoked = service.revoke_permission_grant(grant.grant_id, "done")

    assert service.list_permission_grants(actor_id="actor-1")[0].status == "revoked"
    assert revoked.revoked_at is not None


def test_identity_service_emits_visual_telemetry_events() -> None:
    """Identity mutations emit graph telemetry events."""
    repository = FakeIdentityRepository()
    telemetry = FakeTelemetry()
    service = make_service(repository, telemetry=telemetry)

    actor = service.create_actor(make_actor())
    service.disable_actor(actor.actor_id)
    workspace = service.create_workspace(make_workspace())
    service.archive_workspace(workspace.workspace_id)
    membership = service.add_membership(make_membership())
    service.revoke_membership(membership.membership_id)
    grant = service.create_permission_grant(make_grant())
    service.revoke_permission_grant(grant.grant_id)

    assert [event.event_type for event in telemetry.events] == [
        "actor_created",
        "actor_disabled",
        "workspace_created",
        "workspace_archived",
        "membership_created",
        "membership_revoked",
        "permission_granted",
        "permission_revoked",
    ]


def make_service(
    repository: FakeIdentityRepository,
    *,
    telemetry: object | None = None,
) -> IdentityService:
    """Create a service with a dev owner context."""
    return IdentityService(
        repository=repository,
        policy_adapter=FakePolicyAdapter(),
        actor_context=ActorContext(
            actor_id="actor-1",
            workspace_id="workspace-1",
            roles=["owner"],
            permissions=["identity.actor.create"],
            security_scope=["workspace:workspace-1"],
            dev_mode=True,
        ),
        telemetry_service=telemetry,
    )
