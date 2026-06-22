"""Model output query service."""

from __future__ import annotations

from aion_brain.contracts.output_governance import ModelOutputQuery, ModelOutputQueryResult
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize


class ModelOutputQueryService:
    """Policy-gated query boundary for model outputs."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ModelOutputQueryService:
        return ModelOutputQueryService(self._repository, self._policy_adapter, actor_context)

    def query(self, query: ModelOutputQuery) -> ModelOutputQueryResult:
        authorize(
            self._policy_adapter,
            action_type="model_output.read",
            resource_type="model_output",
            resource_id=query.trace_id,
            scope=query.scope,
            trace_id=query.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        query_call = getattr(self._repository, "query", None)
        result = query_call(query) if callable(query_call) else None
        if isinstance(result, ModelOutputQueryResult):
            return result
        return ModelOutputQueryResult(
            total_count=0, constraints=["repository_unavailable"], metadata={}
        )


__all__ = ["ModelOutputQueryService"]
