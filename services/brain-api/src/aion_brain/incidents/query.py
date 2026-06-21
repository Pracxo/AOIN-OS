"""Incident query service."""

from __future__ import annotations

from aion_brain.contracts.incidents import IncidentQuery, IncidentQueryResult
from aion_brain.dialogue._shared import authorize


class IncidentQueryService:
    """Read incident-owned records through one scope-bound query surface."""

    def __init__(self, repository: object, policy_adapter: object | None = None) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, query: IncidentQuery) -> IncidentQueryResult:
        authorize(
            self._policy_adapter,
            action_type="incident.read",
            resource_type="incident",
            resource_id=query.trace_id,
            scope=query.scope,
            trace_id=query.trace_id,
            risk_level="low",
        )
        list_incidents = getattr(self._repository, "list_incidents", None)
        list_signals = getattr(self._repository, "list_signals", None)
        list_root_causes = getattr(self._repository, "list_root_causes", None)
        list_reviews = getattr(self._repository, "list_recovery_reviews", None)
        incidents = list_incidents(query) if callable(list_incidents) else []
        signals = []
        if callable(list_signals):
            signals = list_signals(
                scope=query.scope,
                trace_id=query.trace_id,
                source_type=query.source_type,
                source_id=query.source_id,
                correlation_key=query.correlation_key,
                include_deleted=query.include_deleted,
                limit=query.limit,
            )
        root_causes = list_root_causes(limit=query.limit) if callable(list_root_causes) else []
        reviews = (
            list_reviews(scope=query.scope, limit=query.limit) if callable(list_reviews) else []
        )
        return IncidentQueryResult(
            incidents=list(incidents or []),
            signals=list(signals or []),
            root_causes=list(root_causes or []),
            recovery_reviews=list(reviews or []),
            total_count=len(incidents or []),
            metadata={"source_mutation": False},
        )


__all__ = ["IncidentQueryService"]
