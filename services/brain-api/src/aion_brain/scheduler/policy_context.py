"""Policy context helpers for the local scheduler."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.scopes import ActorContext


def scheduler_policy_context(
    action_type: str,
    scope: list[str],
    *,
    actor_context: ActorContext | None = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the actor context shape expected by scheduler OPA rules."""

    context = dict(extra or {})
    permissions = (
        actor_context.permissions
        if actor_context is not None and actor_context.permissions
        else [action_type]
    )
    roles = actor_context.roles if actor_context is not None else []
    context["actor_context"] = {
        "actor_id": actor_context.actor_id if actor_context is not None else actor_id,
        "workspace_id": (actor_context.workspace_id if actor_context is not None else workspace_id),
        "roles": roles,
        "permissions": permissions,
        "security_scope": actor_context.security_scope if actor_context is not None else scope,
    }
    return context
