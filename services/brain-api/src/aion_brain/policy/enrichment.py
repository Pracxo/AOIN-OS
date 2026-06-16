"""Policy input enrichment with actor context."""

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext


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
