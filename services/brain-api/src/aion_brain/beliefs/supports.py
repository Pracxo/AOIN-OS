"""Belief support lifecycle service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.beliefs.contradictions import BeliefContradictionService
from aion_brain.beliefs.repository import BeliefRepository
from aion_brain.contracts.beliefs import BeliefSupport, BeliefSupportCreateRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry


class BeliefSupportService:
    """Create, list, and soft-delete claim supports."""

    def __init__(
        self,
        repository: BeliefRepository,
        policy_adapter: object,
        *,
        contradiction_service: BeliefContradictionService | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._contradiction_service = contradiction_service
        self._telemetry_service = telemetry_service

    def create_support(self, request: BeliefSupportCreateRequest) -> BeliefSupport:
        """Create one support relation."""
        claim = self._repository.get_claim(request.claim_id)
        if claim is None:
            raise ValueError("belief_claim_not_found")
        authorize(
            self._policy_adapter,
            action_type="belief.support.create",
            resource_type="belief_support",
            resource_id=request.support_id,
            scope=claim.owner_scope,
            trace_id=claim.trace_id,
            risk_level="low",
            context={"relation_type": request.relation_type},
        )
        support = BeliefSupport(
            support_id=request.support_id or f"belief-support-{uuid4().hex}",
            claim_id=request.claim_id,
            support_type=request.support_type,
            source_type=request.source_type,
            source_id=request.source_id,
            relation_type=request.relation_type,
            strength=request.strength,
            confidence=request.confidence,
            metadata=dict(request.metadata),
            created_at=datetime.now(UTC),
            deleted_at=None,
        )
        stored = self._repository.save_support(support)
        if stored.relation_type == "contradicts" and self._contradiction_service is not None:
            self._contradiction_service.create_contradiction(
                claim_id=stored.claim_id,
                source_type=stored.source_type,
                source_id=stored.source_id,
                contradiction_type="evidence_contradiction",
                severity="medium",
                reason="support_relation_contradicts_claim",
                trace_id=claim.trace_id,
                metadata={"support_id": stored.support_id},
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="belief_support_added",
            node_type="belief",
            node_id=stored.support_id,
            intensity=stored.strength,
            trace_id=claim.trace_id,
            edge_from=stored.source_id,
            edge_to=stored.claim_id,
            payload={"relation_type": stored.relation_type},
        )
        return stored

    def list_supports(
        self,
        claim_id: str,
        include_deleted: bool = False,
    ) -> list[BeliefSupport]:
        """List supports for one claim."""
        claim = self._repository.get_claim(claim_id)
        if claim is None:
            raise ValueError("belief_claim_not_found")
        authorize(
            self._policy_adapter,
            action_type="belief.support.read",
            resource_type="belief_support",
            resource_id=claim_id,
            scope=claim.owner_scope,
            trace_id=claim.trace_id,
        )
        return self._repository.list_supports(claim_id, include_deleted)

    def soft_delete_support(
        self,
        support_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        """Soft-delete one support."""
        support = self._repository.get_support(support_id)
        if support is None:
            raise ValueError("belief_support_not_found")
        claim = self._repository.get_claim(support.claim_id)
        if claim is None:
            raise ValueError("belief_claim_not_found")
        authorize(
            self._policy_adapter,
            action_type="belief.support.delete",
            resource_type="belief_support",
            resource_id=support_id,
            scope=claim.owner_scope,
            actor_id=actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        self._repository.save_support(
            support.model_copy(
                update={
                    "deleted_at": datetime.now(UTC),
                    "metadata": {
                        **support.metadata,
                        "delete_reason": reason,
                        "deleted_by": actor_id,
                    },
                }
            )
        )
        return True
