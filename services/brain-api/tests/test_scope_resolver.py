"""Scope resolver tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.identity import PermissionGrant
from aion_brain.contracts.scopes import ActorContext, ScopeResolution, ScopeResolutionRequest
from aion_brain.scopes.resolver import ScopeResolver
from tests.test_identity_contracts import make_actor, make_grant, make_membership, make_workspace
from tests.test_identity_service import FakeIdentityRepository


class FakeScopeRepository:
    """Scope repository fake."""

    def __init__(self) -> None:
        self.saved: ScopeResolution | None = None

    def save(self, resolution: ScopeResolution) -> ScopeResolution:
        self.saved = resolution
        return resolution


class FakeTelemetry:
    """Telemetry fake."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def test_scope_resolver_applies_actor_context_scopes() -> None:
    """Actor context scopes can allow dev owner requests."""
    repository = FakeIdentityRepository()
    scope_repository = FakeScopeRepository()

    resolution = make_resolver(repository, scope_repository).resolve(
        make_request(),
        make_context(),
    )

    assert resolution.allow is True
    assert "workspace:workspace-1" in resolution.resolved_scopes
    assert scope_repository.saved is resolution


def test_scope_resolver_applies_active_grants() -> None:
    """Active grants contribute permissions."""
    repository = repository_with_identity()
    repository.save_permission_grant(make_grant(permission="memory.read"))

    resolution = make_resolver(repository).resolve(make_request(), make_context(viewer=True))

    assert resolution.allow is True
    assert "memory.read" in resolution.permissions


def test_scope_resolver_ignores_revoked_and_expired_grants() -> None:
    """Inactive grants do not contribute permissions."""
    repository = repository_with_identity()
    repository.save_permission_grant(make_grant(status="revoked", permission="memory.read"))
    repository.save_permission_grant(expired_grant())

    resolution = make_resolver(repository).resolve(make_request(), make_context(viewer=True))

    assert resolution.allow is False
    assert "required_permission_missing" in resolution.constraints


def test_scope_resolver_deny_grant_wins_over_allow_grant() -> None:
    """Deny grants override allowed permissions."""
    repository = repository_with_identity()
    repository.save_permission_grant(make_grant(permission="memory.read"))
    repository.save_permission_grant(
        make_grant("grant-deny", permission="memory.read", effect="deny")
    )

    resolution = make_resolver(repository).resolve(make_request(), make_context(viewer=True))

    assert resolution.allow is False
    assert "permission_denied_by_grant" in resolution.constraints


def test_scope_resolver_blocks_disabled_actor() -> None:
    """Disabled actors have no access."""
    repository = repository_with_identity(actor_status="disabled")
    repository.save_permission_grant(make_grant(permission="memory.read"))

    resolution = make_resolver(repository).resolve(make_request(), make_context(viewer=True))

    assert resolution.allow is False
    assert "actor_disabled" in resolution.constraints


def make_resolver(
    repository: FakeIdentityRepository,
    scope_repository: FakeScopeRepository | None = None,
) -> ScopeResolver:
    """Create a scope resolver."""
    return ScopeResolver(
        identity_repository=repository,
        scope_repository=scope_repository or FakeScopeRepository(),
        telemetry_service=FakeTelemetry(),
    )


def repository_with_identity(actor_status: str = "active") -> FakeIdentityRepository:
    """Create identity repository with actor, workspace, and membership."""
    repository = FakeIdentityRepository()
    repository.save_actor(make_actor(status=actor_status))
    repository.save_workspace(make_workspace())
    repository.save_membership(make_membership(role="viewer"))
    return repository


def make_request() -> ScopeResolutionRequest:
    """Create a scope resolution request."""
    return ScopeResolutionRequest(
        actor_id="actor-1",
        workspace_id="workspace-1",
        requested_scopes=["workspace:workspace-1"],
        action_type="memory.retrieve",
        resource_type="memory",
        resource_id=None,
    )


def make_context(viewer: bool = False) -> ActorContext:
    """Create an actor context."""
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["viewer"] if viewer else ["owner"],
        permissions=[],
        security_scope=["workspace:workspace-1"],
        dev_mode=not viewer,
    )


def expired_grant() -> PermissionGrant:
    """Create an expired grant."""
    return make_grant(
        "grant-expired",
        permission="memory.read",
    ).model_copy(update={"expires_at": datetime.now(UTC) - timedelta(days=1)})
