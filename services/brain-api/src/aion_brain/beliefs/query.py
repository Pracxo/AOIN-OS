"""Belief query service."""

from __future__ import annotations

from aion_brain.beliefs.repository import BeliefRepository
from aion_brain.contracts.beliefs import BeliefContradiction, BeliefQuery, BeliefQueryResult
from aion_brain.dialogue._shared import authorize, emit_telemetry


class BeliefQueryService:
    """Read belief claims through a policy-gated query boundary."""

    def __init__(
        self,
        repository: BeliefRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def query(self, query: BeliefQuery) -> BeliefQueryResult:
        """Return claims, supports, and contradictions."""
        authorize(
            self._policy_adapter,
            action_type="belief.query",
            resource_type="belief_query",
            resource_id=None,
            scope=query.scope,
            risk_level="low",
            context={"statuses": list(query.statuses), "claim_types": list(query.claim_types)},
        )
        claims = self._repository.query_claims(query)
        supports = [
            support
            for claim in claims
            for support in self._repository.list_supports(claim.claim_id)
        ]
        contradictions: list[BeliefContradiction] = []
        for claim in claims:
            contradictions.extend(
                self._repository.list_contradictions(claim_id=claim.claim_id, status=None)
            )
        constraints: list[str] = []
        if any(item.status == "contradicted" for item in claims) and not bool(
            query.metadata.get("include_contradicted")
        ):
            constraints.append("contradicted_claims_present")
        result = BeliefQueryResult(
            claims=claims,
            supports=supports,
            contradictions=contradictions,
            total_count=len(claims),
            constraints=constraints,
            metadata={"query": query.query},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="belief_query_completed",
            node_type="belief",
            node_id=f"belief-query-{abs(hash(str(query.model_dump(mode='json'))))}",
            intensity=min(1.0, len(claims) / max(1, query.limit)),
            trace_id=None,
            payload={"claim_count": len(claims)},
        )
        return result

    def get_recent_supported(self, scope: list[str], limit: int = 50) -> BeliefQueryResult:
        """Convenience helper for local callers."""
        return self.query(BeliefQuery(scope=scope, statuses=["supported"], limit=limit))
