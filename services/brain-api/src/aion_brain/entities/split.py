"""Entity split proposal workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.entities import (
    EntityCreateRequest,
    EntityProposalDecisionRequest,
    EntityRecord,
    EntitySplitProposal,
    EntitySplitProposalCreateRequest,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.entities.normalizer import normalize_entity_name
from aion_brain.entities.repository import EntityRepository


class EntitySplitService:
    """Policy-gated split proposal service."""

    def __init__(
        self,
        repository: EntityRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def propose(
        self,
        request: EntitySplitProposalCreateRequest,
        scope: list[str],
    ) -> EntitySplitProposal:
        """Propose, but do not execute, an entity split."""
        self._require_entity(request.entity_id, scope)
        authorize(
            self._policy_adapter,
            action_type="entity.split.propose",
            resource_type="entity_split",
            resource_id=None,
            scope=scope,
            risk_level="medium",
            context={"proposed_count": len(request.proposed_entities)},
        )
        proposal = EntitySplitProposal(
            split_proposal_id=f"entity-split-{uuid4().hex}",
            entity_id=request.entity_id,
            status="proposed",
            reason=request.reason,
            proposed_entities=list(request.proposed_entities),
            evidence_refs=list(request.evidence_refs),
            approval_request_id=None,
            metadata={},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            resolved_at=None,
        )
        stored = self._repository.save_split_proposal(proposal)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_split_proposed",
            node_type="split",
            node_id=stored.split_proposal_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            edge_from=stored.entity_id,
            edge_to=stored.split_proposal_id,
            payload={"proposed_count": len(stored.proposed_entities)},
        )
        return stored

    def approve(
        self,
        proposal_id: str,
        scope: list[str],
        request: EntityProposalDecisionRequest,
    ) -> EntitySplitProposal:
        """Approve and execute a split into proposed entity records."""
        proposal = self._require_proposal(proposal_id)
        source = self._require_entity(proposal.entity_id, scope)
        authorize(
            self._policy_adapter,
            action_type="entity.split.approve",
            resource_type="entity_split",
            resource_id=proposal_id,
            scope=scope,
            actor_id=request.actor_id,
            risk_level="high",
            approval_present=request.approval_present,
            context={"reason": request.reason},
        )
        for candidate in proposal.proposed_entities:
            create = EntityCreateRequest(
                canonical_name=str(candidate.get("canonical_name") or candidate.get("name")),
                entity_type=candidate.get("entity_type", source.entity_type),
                owner_scope=scope,
                confidence=float(candidate.get("confidence", 0.5)),
                sensitivity=candidate.get("sensitivity", source.sensitivity),
                metadata={"split_from_entity_id": source.entity_id},
                created_by=request.actor_id,
            )
            normalized = normalize_entity_name(create.canonical_name)
            self._repository.save_entity(
                source.model_copy(
                    update={
                        "entity_id": f"entity-{uuid4().hex}",
                        "canonical_name": create.canonical_name,
                        "normalized_name": normalized,
                        "entity_type": create.entity_type,
                        "status": "proposed",
                        "owner_scope": create.owner_scope,
                        "confidence": create.confidence,
                        "sensitivity": create.sensitivity,
                        "metadata": create.metadata,
                        "created_by": create.created_by,
                        "created_at": datetime.now(UTC),
                        "updated_at": datetime.now(UTC),
                        "merged_into_entity_id": None,
                        "archived_at": None,
                        "deleted_at": None,
                    }
                )
            )
        completed = proposal.model_copy(
            update={
                "status": "completed",
                "resolved_at": datetime.now(UTC),
                "metadata": {**proposal.metadata, "approval_reason": request.reason},
            }
        )
        stored = self._repository.save_split_proposal(completed)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_split_completed",
            node_type="split",
            node_id=stored.split_proposal_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            edge_from=stored.entity_id,
            edge_to=stored.split_proposal_id,
            payload={"status": stored.status},
        )
        return stored

    def reject(
        self,
        proposal_id: str,
        scope: list[str],
        request: EntityProposalDecisionRequest,
    ) -> EntitySplitProposal:
        """Reject a split proposal without creating entities."""
        proposal = self._require_proposal(proposal_id)
        self._require_entity(proposal.entity_id, scope)
        authorize(
            self._policy_adapter,
            action_type="entity.split.approve",
            resource_type="entity_split",
            resource_id=proposal_id,
            scope=scope,
            actor_id=request.actor_id,
            risk_level="medium",
            approval_present=request.approval_present,
        )
        rejected = proposal.model_copy(
            update={
                "status": "rejected",
                "resolved_at": datetime.now(UTC),
                "metadata": {**proposal.metadata, "rejection_reason": request.reason},
            }
        )
        return self._repository.save_split_proposal(rejected)

    def list_proposals(
        self,
        scope: list[str],
        status: str | None = "proposed",
    ) -> list[EntitySplitProposal]:
        """List split proposals visible to scope."""
        authorize(
            self._policy_adapter,
            action_type="entity.split.read",
            resource_type="entity_split",
            resource_id=None,
            scope=scope,
        )
        return [
            proposal
            for proposal in self._repository.list_split_proposals(status=status)
            if self._repository.get_entity(proposal.entity_id) is not None
        ]

    def _require_entity(self, entity_id: str, scope: list[str]) -> EntityRecord:
        entity = self._repository.get_entity(entity_id)
        if entity is None or not set(entity.owner_scope).intersection(scope):
            raise ValueError("entity_not_found")
        return entity

    def _require_proposal(self, proposal_id: str) -> EntitySplitProposal:
        proposal = self._repository.get_split_proposal(proposal_id)
        if proposal is None:
            raise ValueError("entity_split_proposal_not_found")
        return proposal
