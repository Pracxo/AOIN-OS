"""Policy-gated situation record service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.situations import (
    SituationCreateRequest,
    SituationQuery,
    SituationQueryResult,
    SituationRecord,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.situations.repository import SituationRepository


class SituationService:
    """Create, read, query, and close situation records."""

    def __init__(
        self,
        repository: SituationRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create(self, request: SituationCreateRequest) -> SituationRecord:
        authorize(
            self._policy_adapter,
            action_type="situation.create",
            resource_type="situation",
            resource_id=request.situation_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"situation_type": request.situation_type},
        )
        now = datetime.now(UTC)
        situation = SituationRecord(
            situation_id=request.situation_id or f"situation-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="active",
            situation_type=request.situation_type,
            title=request.title,
            summary=request.summary,
            owner_scope=request.owner_scope,
            active_goal_ids=request.active_goal_ids,
            active_task_ids=request.active_task_ids,
            active_workflow_run_ids=request.active_workflow_run_ids,
            active_focus_session_ids=request.active_focus_session_ids,
            entity_refs=request.entity_refs,
            belief_refs=request.belief_refs,
            evidence_refs=request.evidence_refs,
            memory_refs=request.memory_refs,
            constraints=request.constraints,
            confidence=request.confidence,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            closed_at=None,
        )
        stored = self._repository.save_situation(situation)
        emit_telemetry(
            self._telemetry_service,
            event_type="situation_created",
            node_type="situation",
            node_id=stored.situation_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "situation_type": stored.situation_type},
        )
        return stored

    def get(self, situation_id: str, scope: list[str]) -> SituationRecord | None:
        authorize(
            self._policy_adapter,
            action_type="situation.read",
            resource_type="situation",
            resource_id=situation_id,
            scope=scope,
        )
        situation = self._repository.get_situation(situation_id)
        if situation is None or not _scope_matches(situation.owner_scope, scope):
            return None
        return situation

    def query(self, query: SituationQuery) -> SituationQueryResult:
        authorize(
            self._policy_adapter,
            action_type="situation.read",
            resource_type="situation",
            resource_id=None,
            scope=query.scope,
            trace_id=query.trace_id,
            actor_id=query.actor_id,
            workspace_id=query.workspace_id,
        )
        situations = self._repository.query_situations(query)
        atoms = []
        if query.include_state_atoms:
            situation_ids = {item.situation_id for item in situations}
            atoms = [
                atom
                for atom in self._repository.list_state_atoms(scope=query.scope, limit=query.limit)
                if atom.situation_id in situation_ids
            ]
        return SituationQueryResult(
            situations=situations,
            state_atoms=atoms,
            total=len(situations),
            constraints=["state_atoms_are_recall_not_truth"] if atoms else [],
        )

    def close(
        self,
        situation_id: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        reason: str,
    ) -> SituationRecord:
        situation = self.get(situation_id, scope)
        if situation is None:
            raise ValueError("situation_not_found")
        authorize(
            self._policy_adapter,
            action_type="situation.update",
            resource_type="situation",
            resource_id=situation_id,
            scope=scope,
            actor_id=actor_id,
            trace_id=situation.trace_id,
            risk_level="low",
            context={"reason": reason},
        )
        now = datetime.now(UTC)
        closed = situation.model_copy(
            update={
                "status": "closed",
                "updated_at": now,
                "closed_at": now,
                "metadata": {**situation.metadata, "close_reason": reason},
            }
        )
        stored = self._repository.save_situation(closed)
        emit_telemetry(
            self._telemetry_service,
            event_type="situation_closed",
            node_type="situation",
            node_id=stored.situation_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"reason": reason},
        )
        return stored

    def status(self, scope: list[str] | None = None) -> dict[str, object]:
        return self._repository.status(scope)


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(requested_scope)))
