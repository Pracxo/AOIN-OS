"""AION-160 hostile header privilege-escalation regression tests."""

from aion_brain.config import Settings
from aion_brain.identity.dev_auth import actor_context_from_headers


class FakeRequest:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


HOSTILE_HEADERS = {
    "X-AION-Actor-ID": "root",
    "X-AION-Workspace-ID": "system",
    "X-AION-Roles": "owner,admin,system",
    "X-AION-Permissions": (
        "*,execution.run,sandbox.run,runtime_permission.grant,secret_ref.create,"
        "connector.create,module.runtime.register,policy.authorize,"
        "model.external.use,release_candidate.write"
    ),
    "X-AION-Security-Scope": "workspace:system,actor:root,global:*,system:admin",
}


def test_hostile_privilege_headers_grant_no_actor_context_power() -> None:
    context = actor_context_from_headers(
        FakeRequest(HOSTILE_HEADERS),
        Settings(env="production", dev_auth_enabled=True),
    )

    assert context.actor_id is None
    assert context.workspace_id is None
    assert context.roles == []
    assert context.permissions == []
    assert context.security_scope == []
    assert context.dev_mode is False
