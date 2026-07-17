"""AION-160 exact development simulation gate tests."""

import pytest

from aion_brain.config import Settings
from aion_brain.identity.dev_auth import (
    actor_context_from_headers,
    development_identity_simulation_enabled,
)


class FakeRequest:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {}


DEV_HEADERS = {
    "X-AION-Actor-ID": "actor-dev",
    "X-AION-Workspace-ID": "workspace-dev",
    "X-AION-Roles": "admin,viewer",
    "X-AION-Permissions": "memory.read,trace.read",
    "X-AION-Security-Scope": "workspace:workspace-dev,actor:actor-dev",
    "X-AION-Correlation-ID": "corr-dev",
    "X-AION-Trace-ID": "trace-dev",
}


def test_development_mode_with_dev_auth_accepts_synthetic_headers() -> None:
    context = actor_context_from_headers(FakeRequest(DEV_HEADERS), Settings())

    assert development_identity_simulation_enabled(Settings()) is True
    assert context.actor_id == "actor-dev"
    assert context.workspace_id == "workspace-dev"
    assert context.roles == ["admin", "viewer"]
    assert context.permissions == ["memory.read", "trace.read"]
    assert context.security_scope == ["workspace:workspace-dev", "actor:actor-dev"]
    assert context.correlation_id == "corr-dev"
    assert context.trace_id == "trace-dev"
    assert context.dev_mode is True


@pytest.mark.parametrize(
    ("env", "dev_auth_enabled"),
    [
        ("production", True),
        ("staging", True),
        ("test", True),
        ("ci", True),
        ("local", True),
        ("dev", True),
        ("", True),
        ("development", False),
    ],
)
def test_only_exact_development_gate_accepts_headers(
    env: str,
    dev_auth_enabled: bool,
) -> None:
    settings = Settings(env=env, dev_auth_enabled=dev_auth_enabled)
    context = actor_context_from_headers(FakeRequest(DEV_HEADERS), settings)

    assert development_identity_simulation_enabled(settings) is False
    assert context.actor_id is None
    assert context.workspace_id is None
    assert context.roles == []
    assert context.permissions == []
    assert context.security_scope == []
    assert context.dev_mode is False
