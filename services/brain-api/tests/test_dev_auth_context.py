"""Development actor context tests."""

from aion_brain.config import Settings
from aion_brain.identity.dev_auth import actor_context_from_headers


class FakeRequest:
    """Tiny request fake with headers."""

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {}


def test_dev_auth_creates_default_actor_context_in_development() -> None:
    """Development mode creates a local owner context."""
    context = actor_context_from_headers(FakeRequest(), Settings())

    assert context.actor_id == "dev-user"
    assert context.workspace_id == "dev-workspace"
    assert context.roles == ["owner"]
    assert "workspace:dev-workspace" in context.security_scope
    assert context.dev_mode is True


def test_dev_auth_parses_header_roles_permissions_and_scopes() -> None:
    """Development headers override defaults."""
    context = actor_context_from_headers(
        FakeRequest(
            {
                "X-AION-Actor-ID": "actor-2",
                "X-AION-Workspace-ID": "workspace-2",
                "X-AION-Roles": "admin, viewer",
                "X-AION-Permissions": "memory.read,trace.read",
                "X-AION-Security-Scope": "workspace:workspace-2,actor:actor-2",
            }
        ),
        Settings(),
    )

    assert context.actor_id == "actor-2"
    assert context.roles == ["admin", "viewer"]
    assert context.permissions == ["memory.read", "trace.read"]
    assert context.security_scope == ["workspace:workspace-2", "actor:actor-2"]


def test_dev_auth_does_not_create_implicit_owner_outside_development() -> None:
    """Non-development mode does not invent owner permissions."""
    context = actor_context_from_headers(
        FakeRequest(),
        Settings(env="production", dev_auth_enabled=True),
    )

    assert context.actor_id is None
    assert context.roles == []
    assert context.permissions == []
    assert context.dev_mode is False
