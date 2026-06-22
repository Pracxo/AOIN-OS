"""Action proposal query service."""

from __future__ import annotations

from aion_brain.contracts.action_proposals import ActionProposalQuery, ActionProposalQueryResult
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize


class ActionProposalQueryService:
    """Query action proposal records through policy."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ActionProposalQueryService:
        return ActionProposalQueryService(
            self._repository,
            self._policy_adapter,
            actor_context=actor_context,
        )

    def query(self, query: ActionProposalQuery) -> ActionProposalQueryResult:
        authorize(
            self._policy_adapter,
            action_type="action_proposal.read",
            resource_type="action_proposal",
            resource_id=query.trace_id,
            scope=query.scope,
            trace_id=query.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        run_query = getattr(self._repository, "query", None)
        if not callable(run_query):
            return ActionProposalQueryResult(total_count=0)
        result = run_query(query)
        return (
            result
            if isinstance(result, ActionProposalQueryResult)
            else ActionProposalQueryResult(total_count=0)
        )


__all__ = ["ActionProposalQueryService"]
