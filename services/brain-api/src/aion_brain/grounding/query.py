"""Grounding query service."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.citations import GroundingQueryResult
from aion_brain.contracts.grounding import GroundingQuery
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize


class GroundingQueryService:
    """Query grounding, citation, unsupported, and coverage records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object,
        *,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> GroundingQueryService:
        return GroundingQueryService(
            self._repository,
            self._policy_adapter,
            actor_context=actor_context,
        )

    def query(self, query: GroundingQuery) -> GroundingQueryResult:
        """Return AION-owned grounding query contracts only."""

        authorize(
            self._policy_adapter,
            action_type="grounding.query",
            resource_type="grounding",
            resource_id=query.response_id or query.explanation_id or query.trace_id,
            scope=query.scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        sources = _call(
            self._repository,
            "list_sources",
            query.scope,
            trace_id=query.trace_id,
            source_type=query.source_type,
            trust_level=query.trust_level,
            include_deleted=query.include_deleted,
            limit=query.limit,
        )
        citations = _call(
            self._repository,
            "list_citations",
            response_id=query.response_id,
            explanation_id=query.explanation_id,
            trace_id=query.trace_id,
            include_deleted=query.include_deleted,
            limit=query.limit,
        )
        citation_maps = _call(
            self._repository,
            "list_citation_maps",
            response_id=query.response_id,
            trace_id=query.trace_id,
            limit=query.limit,
        )
        unsupported = _call(
            self._repository,
            "list_unsupported",
            response_id=query.response_id,
            explanation_id=query.explanation_id,
            trace_id=query.trace_id,
            limit=query.limit,
        )
        coverage = _call(
            self._repository,
            "list_coverage_reports",
            response_id=query.response_id,
            explanation_id=query.explanation_id,
            trace_id=query.trace_id,
            limit=query.limit,
        )
        return GroundingQueryResult(
            sources=sources,
            citations=citations,
            citation_maps=citation_maps,
            unsupported_statements=unsupported,
            coverage_reports=coverage,
            total_count=(
                len(sources)
                + len(citations)
                + len(citation_maps)
                + len(unsupported)
                + len(coverage)
            ),
            constraints=[],
            metadata={"limit": query.limit},
        )


def _call(repository: object, name: str, *args: object, **kwargs: object) -> list[Any]:
    method = getattr(repository, name, None)
    if callable(method):
        result = method(*args, **kwargs)
        return list(result) if isinstance(result, list) else []
    return []


__all__ = ["GroundingQueryService"]
