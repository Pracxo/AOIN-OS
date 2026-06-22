"""Entity merge proposal workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.entities import (
    EntityMergeProposal,
    EntityMergeProposalCreateRequest,
    EntityProposalDecisionRequest,
    EntityRecord,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.entities.repository import EntityRepository


class EntityMergeService:
    """Policy-gated merge proposal service with no auto-merge path."""

    def __init__(
        self,
        repository: EntityRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings

    def propose(
        self,
        request: EntityMergeProposalCreateRequest,
        scope: list[str],
    ) -> EntityMergeProposal:
        """Propose, but do not execute, an entity merge."""
        primary = self._require_entity(request.primary_entity_id, scope)
        duplicate = self._require_entity(request.duplicate_entity_id, scope)
        authorize(
            self._policy_adapter,
            action_type="entity.merge.propose",
            resource_type="entity_merge",
            resource_id=None,
            scope=scope,
            trace_id=request.trace_id,
            actor_id=request.created_by,
            risk_level="medium",
        )
        proposal = EntityMergeProposal(
            merge_proposal_id=f"entity-merge-{uuid4().hex}",
            trace_id=request.trace_id,
            primary_entity_id=primary.entity_id,
            duplicate_entity_id=duplicate.entity_id,
            status="proposed",
            score=_merge_score(primary.normalized_name, duplicate.normalized_name),
            reason=request.reason,
            evidence_refs=list(request.evidence_refs),
            approval_request_id=None,
            metadata={"auto_merge": False},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            resolved_at=None,
        )
        stored = self._repository.save_merge_proposal(proposal)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_merge_proposed",
            node_type="merge",
            node_id=stored.merge_proposal_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            edge_from=stored.duplicate_entity_id,
            edge_to=stored.primary_entity_id,
            payload={"requires_approval": True},
        )
        return stored

    def approve(
        self,
        proposal_id: str,
        scope: list[str],
        request: EntityProposalDecisionRequest,
    ) -> EntityMergeProposal:
        """Approve and execute a merge when explicit approval is present."""
        proposal = self._require_proposal(proposal_id)
        self._require_entity(proposal.primary_entity_id, scope)
        duplicate = self._require_entity(proposal.duplicate_entity_id, scope)
        if _setting_bool(self._settings, "entity_merge_requires_approval", True):
            if not request.approval_present:
                raise PermissionError("entity_merge_requires_approval")
        authorize(
            self._policy_adapter,
            action_type="entity.merge.approve",
            resource_type="entity_merge",
            resource_id=proposal_id,
            scope=scope,
            actor_id=request.actor_id,
            risk_level="high",
            approval_present=request.approval_present,
            context={"reason": request.reason},
        )
        self._repository.save_entity(
            duplicate.model_copy(
                update={
                    "status": "merged",
                    "merged_into_entity_id": proposal.primary_entity_id,
                    "updated_at": datetime.now(UTC),
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
        stored = self._repository.save_merge_proposal(completed)
        emit_telemetry(
            self._telemetry_service,
            event_type="entity_merge_completed",
            node_type="merge",
            node_id=stored.merge_proposal_id,
            intensity=stored.score,
            trace_id=stored.trace_id,
            edge_from=stored.duplicate_entity_id,
            edge_to=stored.primary_entity_id,
            payload={"status": stored.status},
        )
        return stored

    def reject(
        self,
        proposal_id: str,
        scope: list[str],
        request: EntityProposalDecisionRequest,
    ) -> EntityMergeProposal:
        """Reject a merge proposal."""
        proposal = self._require_proposal(proposal_id)
        self._require_entity(proposal.primary_entity_id, scope)
        authorize(
            self._policy_adapter,
            action_type="entity.merge.approve",
            resource_type="entity_merge",
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
        return self._repository.save_merge_proposal(rejected)

    def list_proposals(
        self,
        scope: list[str],
        status: str | None = "proposed",
    ) -> list[EntityMergeProposal]:
        """List merge proposals visible to scope."""
        authorize(
            self._policy_adapter,
            action_type="entity.merge.read",
            resource_type="entity_merge",
            resource_id=None,
            scope=scope,
        )
        proposals = self._repository.list_merge_proposals(status=status)
        return [
            proposal
            for proposal in proposals
            if self._repository.get_entity(proposal.primary_entity_id) is not None
        ]

    def _require_entity(self, entity_id: str, scope: list[str]) -> EntityRecord:
        entity = self._repository.get_entity(entity_id)
        if entity is None or not set(entity.owner_scope).intersection(scope):
            raise ValueError("entity_not_found")
        return entity

    def _require_proposal(self, proposal_id: str) -> EntityMergeProposal:
        proposal = self._repository.get_merge_proposal(proposal_id)
        if proposal is None:
            raise ValueError("entity_merge_proposal_not_found")
        return proposal


def _merge_score(left: str, right: str) -> float:
    if left == right:
        return 1.0
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens.intersection(right_tokens)) / len(left_tokens.union(right_tokens))


def _setting_bool(settings: object | None, name: str, default: bool) -> bool:
    value = getattr(settings, name, default)
    return bool(value)
