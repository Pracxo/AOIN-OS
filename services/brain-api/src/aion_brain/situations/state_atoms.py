"""Policy-gated state atom service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.temporal_state import StateAtom, StateAtomCreateRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.situations.repository import SituationRepository


class StateAtomService:
    """Create, read, list, supersede, and soft-delete projected state atoms."""

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

    def create(self, request: StateAtomCreateRequest) -> StateAtom:
        authorize(
            self._policy_adapter,
            action_type="situation.atom.create",
            resource_type="state_atom",
            resource_id=request.state_atom_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            risk_level="low",
            context={"source_type": request.source_type, "atom_type": request.atom_type},
        )
        now = datetime.now(UTC)
        atom = StateAtom(
            state_atom_id=request.state_atom_id or f"state-atom-{uuid4().hex}",
            situation_id=request.situation_id,
            trace_id=request.trace_id,
            atom_type=request.atom_type,
            source_type=request.source_type,
            source_id=request.source_id,
            subject_ref=request.subject_ref,
            predicate=request.predicate,
            object_ref=request.object_ref,
            value=request.value,
            status=request.status,
            confidence=request.confidence,
            sensitivity=request.sensitivity,
            observed_at=request.observed_at or now,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
            owner_scope=request.owner_scope,
            evidence_refs=request.evidence_refs,
            belief_refs=request.belief_refs,
            entity_refs=request.entity_refs,
            metadata=request.metadata,
            created_at=now,
            superseded_at=None,
            deleted_at=None,
        )
        stored = self._repository.save_state_atom(atom)
        emit_telemetry(
            self._telemetry_service,
            event_type="state_atom_created",
            node_type="state_atom",
            node_id=stored.state_atom_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "atom_type": stored.atom_type},
        )
        return stored

    def get(self, state_atom_id: str, scope: list[str]) -> StateAtom | None:
        authorize(
            self._policy_adapter,
            action_type="situation.atom.read",
            resource_type="state_atom",
            resource_id=state_atom_id,
            scope=scope,
        )
        atom = self._repository.get_state_atom(state_atom_id)
        if atom is None or atom.deleted_at is not None:
            return None
        if not set(atom.owner_scope).intersection(scope):
            return None
        return atom

    def list_atoms(
        self,
        *,
        scope: list[str],
        situation_id: str | None = None,
        trace_id: str | None = None,
        statuses: list[str] | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[StateAtom]:
        authorize(
            self._policy_adapter,
            action_type="situation.atom.read",
            resource_type="state_atom",
            resource_id=situation_id,
            scope=scope,
            trace_id=trace_id,
        )
        return self._repository.list_state_atoms(
            scope=scope,
            situation_id=situation_id,
            trace_id=trace_id,
            statuses=statuses,
            source_type=source_type,
            source_id=source_id,
            include_deleted=include_deleted,
            limit=limit,
        )

    def supersede(self, state_atom_id: str, scope: list[str]) -> StateAtom:
        atom = self.get(state_atom_id, scope)
        if atom is None:
            raise ValueError("state_atom_not_found")
        authorize(
            self._policy_adapter,
            action_type="situation.atom.update",
            resource_type="state_atom",
            resource_id=state_atom_id,
            scope=scope,
            trace_id=atom.trace_id,
            risk_level="low",
        )
        stored = self._repository.save_state_atom(
            atom.model_copy(update={"status": "superseded", "superseded_at": datetime.now(UTC)})
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="state_atom_superseded",
            node_type="state_atom",
            node_id=stored.state_atom_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope},
        )
        return stored

    def soft_delete(self, state_atom_id: str, scope: list[str]) -> StateAtom:
        atom = self.get(state_atom_id, scope)
        if atom is None:
            raise ValueError("state_atom_not_found")
        authorize(
            self._policy_adapter,
            action_type="situation.atom.delete",
            resource_type="state_atom",
            resource_id=state_atom_id,
            scope=scope,
            trace_id=atom.trace_id,
            risk_level="medium",
        )
        return self._repository.save_state_atom(
            atom.model_copy(update={"deleted_at": datetime.now(UTC)})
        )
