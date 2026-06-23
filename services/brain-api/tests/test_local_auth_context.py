from __future__ import annotations

from aion_brain.contracts.local_auth import DevIdentitySimulationRequest
from aion_brain.local_auth.context import build_local_auth_context
from aion_brain.local_auth.identity import build_local_operator_identity


def test_build_local_auth_context_never_grants_privileged_actions() -> None:
    identity = build_local_operator_identity(
        DevIdentitySimulationRequest(
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
        )
    )

    context = build_local_auth_context(identity, trace_id="trace-local-auth-1")

    assert context.read_allowed is True
    assert context.dry_run_allowed is True
    assert context.write_allowed is False
    assert context.execute_allowed is False
    assert context.activation_allowed is False
    assert context.external_calls_allowed is False
    assert context.production_auth is False
    assert context.session_present is False
    assert context.credentials_present is False
