"""Belief contradiction detection and lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.beliefs.normalizer import normalize_claim_text
from aion_brain.beliefs.repository import BeliefRepository
from aion_brain.contracts.beliefs import (
    BeliefClaim,
    BeliefContradiction,
    BeliefContradictionType,
    BeliefQuery,
    BeliefSeverity,
    BeliefSourceType,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry


class BeliefContradictionService:
    """Detect, create, list, and resolve contradictions."""

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

    def detect_for_claim(self, claim_id: str) -> list[BeliefContradiction]:
        """Detect deterministic v0.1 contradictions for one claim."""
        claim = self._require_claim(claim_id)
        existing = self._repository.list_contradictions(claim_id=claim_id, status="open")
        detected: list[BeliefContradiction] = []
        all_claims = self._repository.query_claims(_query_all(scope=claim.owner_scope, limit=500))
        for other in all_claims:
            if other.claim_id == claim.claim_id or other.deleted_at is not None:
                continue
            if _direct_negation_conflict(claim, other) or _metadata_fact_conflict(claim, other):
                if any(item.contradicting_claim_id == other.claim_id for item in existing):
                    continue
                detected.append(
                    self.create_contradiction(
                        claim_id=claim.claim_id,
                        contradicting_claim_id=other.claim_id,
                        source_type=other.source_type,
                        source_id=other.source_id or other.claim_id,
                        contradiction_type="direct_claim_conflict",
                        severity="high",
                        reason="deterministic_claim_conflict",
                        trace_id=claim.trace_id or other.trace_id,
                        metadata={"detected_by": "belief_contradiction_service"},
                    )
                )
        return detected

    def create_contradiction(
        self,
        *,
        claim_id: str,
        source_type: str,
        source_id: str,
        contradiction_type: str = "generic",
        severity: str = "medium",
        reason: str,
        trace_id: str | None = None,
        contradicting_claim_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> BeliefContradiction:
        """Create one contradiction record."""
        claim = self._require_claim(claim_id)
        authorize(
            self._policy_adapter,
            action_type="belief.contradiction.create",
            resource_type="belief_contradiction",
            resource_id=claim_id,
            scope=claim.owner_scope,
            trace_id=trace_id or claim.trace_id,
            risk_level="medium",
            context={"severity": severity, "contradiction_type": contradiction_type},
        )
        contradiction = BeliefContradiction(
            contradiction_id=f"belief-contradiction-{uuid4().hex}",
            trace_id=trace_id or claim.trace_id,
            claim_id=claim_id,
            contradicting_claim_id=contradicting_claim_id,
            source_type=cast(BeliefSourceType, source_type),
            source_id=source_id,
            contradiction_type=cast(BeliefContradictionType, contradiction_type),
            severity=cast(BeliefSeverity, severity),
            status="open",
            reason=reason,
            metadata=metadata or {},
            created_at=datetime.now(UTC),
            resolved_at=None,
        )
        stored = self._repository.save_contradiction(contradiction)
        emit_telemetry(
            self._telemetry_service,
            event_type="belief_contradiction_detected",
            node_type="contradiction",
            node_id=stored.contradiction_id,
            intensity=1.0 if stored.severity in {"high", "critical"} else 0.7,
            trace_id=stored.trace_id,
            edge_from=claim_id,
            edge_to=contradicting_claim_id,
            payload={"severity": stored.severity, "status": stored.status},
        )
        return stored

    def list_contradictions(
        self,
        scope: list[str],
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[BeliefContradiction]:
        """List contradictions visible to a scope."""
        authorize(
            self._policy_adapter,
            action_type="belief.contradiction.read",
            resource_type="belief_contradiction",
            resource_id=None,
            scope=scope,
        )
        rows = self._repository.list_contradictions(status=status, severity=severity, limit=limit)
        return [
            item
            for item in rows
            if (claim := self._repository.get_claim(item.claim_id)) is not None
            and bool(set(claim.owner_scope) & set(scope))
        ][:limit]

    def resolve(
        self,
        contradiction_id: str,
        actor_id: str | None,
        reason: str,
    ) -> BeliefContradiction:
        """Resolve one contradiction record."""
        contradiction = self._require_contradiction(contradiction_id)
        claim = self._require_claim(contradiction.claim_id)
        authorize(
            self._policy_adapter,
            action_type="belief.contradiction.resolve",
            resource_type="belief_contradiction",
            resource_id=contradiction_id,
            scope=claim.owner_scope,
            actor_id=actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        stored = self._repository.save_contradiction(
            contradiction.model_copy(
                update={
                    "status": "resolved",
                    "resolved_at": datetime.now(UTC),
                    "metadata": {
                        **contradiction.metadata,
                        "resolved_by": actor_id,
                        "resolve_reason": reason,
                    },
                }
            )
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="belief_contradiction_resolved",
            node_type="contradiction",
            node_id=stored.contradiction_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"status": stored.status},
        )
        return stored

    def _require_claim(self, claim_id: str) -> BeliefClaim:
        claim = self._repository.get_claim(claim_id)
        if claim is None:
            raise ValueError("belief_claim_not_found")
        return claim

    def _require_contradiction(self, contradiction_id: str) -> BeliefContradiction:
        contradiction = self._repository.get_contradiction(contradiction_id)
        if contradiction is None:
            raise ValueError("belief_contradiction_not_found")
        return contradiction


def _direct_negation_conflict(first: BeliefClaim, second: BeliefClaim) -> bool:
    first_text = normalize_claim_text(first.claim_text)
    second_text = normalize_claim_text(second.claim_text)
    return first_text == f"not {second_text}" or second_text == f"not {first_text}"


def _metadata_fact_conflict(first: BeliefClaim, second: BeliefClaim) -> bool:
    first_key = first.metadata.get("fact_key")
    second_key = second.metadata.get("fact_key")
    if first_key is None or first_key != second_key:
        return False
    first_value = first.metadata.get("fact_value")
    second_value = second.metadata.get("fact_value")
    return first_value is not None and second_value is not None and first_value != second_value


def _query_all(scope: list[str], limit: int) -> BeliefQuery:
    return BeliefQuery(scope=scope, limit=limit)
