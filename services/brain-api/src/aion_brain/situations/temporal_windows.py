"""Temporal state window service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.temporal_state import TemporalStateWindow, TemporalStateWindowRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.situations.repository import SituationRepository


class TemporalStateWindowService:
    """Create and read deterministic state windows."""

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

    def create(self, request: TemporalStateWindowRequest) -> TemporalStateWindow:
        authorize(
            self._policy_adapter,
            action_type="situation.temporal_window.create",
            resource_type="temporal_state_window",
            resource_id=request.temporal_window_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
        )
        window = TemporalStateWindow(
            temporal_window_id=request.temporal_window_id or f"temporal-window-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            window_type=request.window_type,
            owner_scope=request.owner_scope,
            start_at=request.start_at,
            end_at=request.end_at,
            state_atom_ids=request.state_atom_ids,
            event_ids=request.event_ids,
            situation_ids=request.situation_ids,
            summary=request.summary
            or _summary(request.window_type, len(request.state_atom_ids), len(request.event_ids)),
            metadata=request.metadata,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_temporal_window(window)
        emit_telemetry(
            self._telemetry_service,
            event_type="temporal_state_window_created",
            node_type="temporal_window",
            node_id=stored.temporal_window_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"window_type": stored.window_type, "owner_scope": stored.owner_scope},
        )
        return stored

    def get(self, temporal_window_id: str, scope: list[str]) -> TemporalStateWindow | None:
        authorize(
            self._policy_adapter,
            action_type="situation.temporal_window.read",
            resource_type="temporal_state_window",
            resource_id=temporal_window_id,
            scope=scope,
        )
        window = self._repository.get_temporal_window(temporal_window_id)
        if window is None or not set(window.owner_scope).intersection(scope):
            return None
        return window

    def list_windows(
        self,
        *,
        scope: list[str],
        trace_id: str | None = None,
        window_type: str | None = None,
        limit: int = 100,
    ) -> list[TemporalStateWindow]:
        authorize(
            self._policy_adapter,
            action_type="situation.temporal_window.read",
            resource_type="temporal_state_window",
            resource_id=None,
            scope=scope,
            trace_id=trace_id,
        )
        return self._repository.list_temporal_windows(
            scope=scope,
            trace_id=trace_id,
            window_type=window_type,
            limit=limit,
        )


def _summary(window_type: str, atom_count: int, event_count: int) -> str:
    return f"{window_type} window with {atom_count} state atoms and {event_count} events."
