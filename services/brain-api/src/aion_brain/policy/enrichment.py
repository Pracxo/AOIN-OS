"""Policy input enrichment with actor context."""

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import DEV_PERMISSIONS


class PolicyInputEnricher:
    """Adds actor-context data to generic policy requests."""

    def enrich(
        self,
        policy_request: PolicyRequest,
        actor_context: ActorContext,
    ) -> PolicyRequest:
        """Return a policy request enriched with actor and scope context."""
        context = {
            **policy_request.context,
            "actor_context": actor_context.model_dump(mode="json"),
            "resolved_security_scope": actor_context.security_scope,
            "roles": actor_context.roles,
            "permissions": actor_context.permissions,
            "workspace_id": actor_context.workspace_id,
            "dev_mode": actor_context.dev_mode,
        }
        return policy_request.model_copy(
            update={
                "actor_id": policy_request.actor_id or actor_context.actor_id,
                "workspace_id": policy_request.workspace_id or actor_context.workspace_id,
                "security_scope": policy_request.security_scope or actor_context.security_scope,
                "context": context,
            }
        )


def enrich_with_internal_dev_actor(
    policy_request: PolicyRequest,
    settings: Settings,
    *,
    scope: list[str],
    permissions: list[str] | None = None,
) -> PolicyRequest:
    """Attach local dev actor context for service-owned internal checks."""
    if settings.env != "development" or not settings.dev_auth_enabled:
        return policy_request

    actor_id = policy_request.actor_id or settings.default_dev_actor_id
    workspace_id = policy_request.workspace_id or settings.default_dev_workspace_id
    actor_context = ActorContext(
        actor_id=actor_id,
        actor_type="system",
        workspace_id=workspace_id,
        roles=["owner"],
        permissions=permissions or list(DEV_PERMISSIONS),
        security_scope=scope
        or [
            f"workspace:{workspace_id}",
            f"actor:{actor_id}",
        ],
        correlation_id=None,
        trace_id=policy_request.trace_id,
        dev_mode=True,
    )
    return PolicyInputEnricher().enrich(policy_request, actor_context)
