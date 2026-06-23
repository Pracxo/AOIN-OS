"""Governed operator action query service."""

from __future__ import annotations

from aion_brain.contracts.operator_actions import OperatorActionQuery, OperatorActionQueryResult
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize


class OperatorActionQueryService:
    """Query operator action records through policy."""

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

    def with_actor_context(self, actor_context: ActorContext) -> OperatorActionQueryService:
        return OperatorActionQueryService(
            self._repository,
            self._policy_adapter,
            actor_context=actor_context,
        )

    def query(self, query: OperatorActionQuery) -> OperatorActionQueryResult:
        authorize(
            self._policy_adapter,
            action_type="operator_action.query",
            resource_type="operator_action_request",
            resource_id=None,
            scope=query.scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        run_query = getattr(self._repository, "query", None)
        if not callable(run_query):
            return OperatorActionQueryResult(total_count=0)
        result = run_query(query)
        return (
            result
            if isinstance(result, OperatorActionQueryResult)
            else OperatorActionQueryResult(total_count=0)
        )


__all__ = ["OperatorActionQueryService"]
