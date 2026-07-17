"""AION-160 fail-closed actor-context tests."""

from aion_brain.config import Settings
from aion_brain.identity.dev_auth import actor_context_from_headers


class FakeRequest:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {}


HOSTILE_HEADERS = {
    "X-AION-Actor-ID": "root",
    "X-AION-Workspace-ID": "system",
    "X-AION-Roles": "owner,admin,system",
    "X-AION-Permissions": "*,execution.run,sandbox.run",
    "X-AION-Security-Scope": "workspace:system,actor:root,global:*,system:admin",
    "X-AION-Correlation-ID": "corr-header",
    "X-AION-Trace-ID": "trace-header",
}


def test_non_development_identity_headers_are_ignored_fail_closed() -> None:
    context = actor_context_from_headers(
        FakeRequest(HOSTILE_HEADERS),
        Settings(env="production", dev_auth_enabled=True),
    )

    assert context.actor_id is None
    assert context.actor_type is None
    assert context.workspace_id is None
    assert context.roles == []
    assert context.permissions == []
    assert context.security_scope == []
    assert context.correlation_id is None
    assert context.trace_id is None
    assert context.dev_mode is False


def test_disabled_development_auth_ignores_headers() -> None:
    context = actor_context_from_headers(
        FakeRequest(HOSTILE_HEADERS),
        Settings(env="development", dev_auth_enabled=False),
    )

    assert context.actor_id is None
    assert context.permissions == []
    assert context.security_scope == []
    assert context.dev_mode is False
