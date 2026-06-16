"""Context continuity service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.situations import ContextContinuityRecord, ContextContinuityRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.situations.repository import SituationRepository


class ContextContinuityService:
    """Record and list deterministic context continuity decisions."""

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

    def record(self, request: ContextContinuityRequest) -> ContextContinuityRecord:
        authorize(
            self._policy_adapter,
            action_type="situation.continuity.record",
            resource_type="context_continuity",
            resource_id=request.continuity_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"continuity_type": request.continuity_type},
        )
        carried = _unique([*request.carried_refs, *request.refs])[:100]
        dropped = _drop_refs(carried, request.dropped_refs)
        record = ContextContinuityRecord(
            continuity_id=request.continuity_id or f"continuity-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            dialogue_session_id=request.dialogue_session_id,
            focus_session_id=request.focus_session_id,
            situation_id=request.situation_id,
            continuity_type=request.continuity_type,
            status="warning" if dropped else "recorded",
            carried_refs=[item for item in carried if item not in dropped],
            dropped_refs=dropped,
            constraints=[
                *request.constraints,
                *(["continuity_refs_dropped:" + str(len(dropped))] if dropped else []),
            ],
            reason=request.reason,
            metadata={**request.metadata, "owner_scope": request.owner_scope},
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_continuity(record)
        emit_telemetry(
            self._telemetry_service,
            event_type="context_continuity_recorded",
            node_type="continuity",
            node_id=stored.continuity_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"continuity_type": stored.continuity_type, "status": stored.status},
        )
        return stored

    def list_records(
        self,
        *,
        scope: list[str],
        trace_id: str | None = None,
        dialogue_session_id: str | None = None,
        focus_session_id: str | None = None,
        situation_id: str | None = None,
        limit: int = 100,
    ) -> list[ContextContinuityRecord]:
        authorize(
            self._policy_adapter,
            action_type="situation.continuity.read",
            resource_type="context_continuity",
            resource_id=situation_id,
            scope=scope,
            trace_id=trace_id,
        )
        return self._repository.list_continuity(
            scope=scope,
            trace_id=trace_id,
            dialogue_session_id=dialogue_session_id,
            focus_session_id=focus_session_id,
            situation_id=situation_id,
            limit=limit,
        )


def _drop_refs(carried: list[str], explicit: list[str]) -> list[str]:
    dropped = set(explicit)
    for ref in carried:
        text = ref.lower()
        if any(marker in text for marker in ("stale", "contradicted", "expired", "deleted")):
            dropped.add(ref)
    return sorted(dropped)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value and value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
