"""Local auth context derivation."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.contracts.local_auth import LocalAuthContext, LocalOperatorIdentity, utc_now
from aion_brain.local_auth.roles import LocalRoleService


def build_local_auth_context(
    identity: LocalOperatorIdentity,
    *,
    trace_id: str | None = None,
    role_service: LocalRoleService | None = None,
) -> LocalAuthContext:
    """Build a non-privileged local auth context from a synthetic identity."""
    service = role_service or LocalRoleService()
    merged = service.permissions_for_roles(identity.roles)
    dry_run_actions = merged.get("dry_run_actions", [])
    review_actions = merged.get("review_actions", [])
    return LocalAuthContext(
        local_auth_context_id=f"local-auth-context-{uuid4().hex}",
        trace_id=trace_id,
        actor_id=identity.actor_id,
        workspace_id=identity.workspace_id,
        roles=identity.roles,
        owner_scope=identity.owner_scope,
        read_allowed=bool(merged.get("read_views")),
        dry_run_allowed=bool(dry_run_actions),
        review_allowed=bool(review_actions),
        write_allowed=False,
        execute_allowed=False,
        activation_allowed=False,
        external_calls_allowed=False,
        production_auth=False,
        session_present=False,
        credentials_present=False,
        metadata={
            "synthetic": True,
            "role_constraints": merged.get("constraints", []),
            "local_identity_id": identity.local_identity_id,
            "local_session_preview_compatible": True,
        },
        created_at=utc_now(),
    )


__all__ = ["build_local_auth_context"]
