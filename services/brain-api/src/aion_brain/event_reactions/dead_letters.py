"""Dead-letter service for failed event reaction actions."""

from datetime import UTC, datetime
from typing import Protocol, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.event_reactions import (
    EventDeadLetterRecord,
    EventDispatchRecord,
    EventDispatchRequest,
    EventReactionAction,
)
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.event_reactions.repository import EventReactionRepository
from aion_brain.events.repository import EventRepository
from aion_brain.policy.base import PolicyAdapter


class EventReactionRouterProtocol(Protocol):
    """Small replay boundary to avoid a hard router import cycle."""

    def dispatch(self, request: EventDispatchRequest) -> EventDispatchRecord:
        """Dispatch one event through the event reaction router."""
        ...


class EventDeadLetterService:
    """Manage failed reaction actions and policy-gated replays."""

    def __init__(
        self,
        *,
        repository: EventReactionRepository,
        event_repository: EventRepository,
        policy_adapter: PolicyAdapter,
        settings: Settings,
        telemetry_service: object | None = None,
        router: EventReactionRouterProtocol | None = None,
    ) -> None:
        self._repository = repository
        self._event_repository = event_repository
        self._policy_adapter = policy_adapter
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._router = router

    def set_router(self, router: EventReactionRouterProtocol) -> None:
        """Attach the router after both services are constructed."""
        self._router = router

    def create_dead_letter(
        self,
        *,
        dispatch_id: str,
        action: EventReactionAction,
        event: AIONEvent,
        reason: str,
        error: dict[str, object],
    ) -> EventDeadLetterRecord:
        """Create an open dead-letter record for a failed action."""
        if not self._settings.event_dead_letter_enabled:
            return EventDeadLetterRecord(
                dead_letter_id=f"dead-letter-disabled-{uuid4().hex}",
                dispatch_id=dispatch_id,
                reaction_action_id=action.reaction_action_id,
                event_id=event.event_id,
                subscription_id=action.subscription_id,
                trace_id=event.trace_id,
                reason="dead_letter_disabled",
                error={"original_reason": reason},
                status="dismissed",
                replay_count=0,
                created_at=datetime.now(UTC),
                resolved_at=datetime.now(UTC),
            )
        record = EventDeadLetterRecord(
            dead_letter_id=f"dead-letter-{uuid4().hex}",
            dispatch_id=dispatch_id,
            reaction_action_id=action.reaction_action_id,
            event_id=event.event_id,
            subscription_id=action.subscription_id,
            trace_id=event.trace_id,
            reason=reason,
            error={**error, "owner_scope": event.security_scope or ["workspace:main"]},
            status="open",
            replay_count=0,
            created_at=datetime.now(UTC),
            resolved_at=None,
        )
        saved = self._repository.save_dead_letter(record)
        _emit(
            self._telemetry_service,
            "event_dead_lettered",
            "dead_letter",
            saved.dead_letter_id,
            saved.trace_id,
            {"event_id": saved.event_id, "subscription_id": saved.subscription_id},
        )
        return saved

    def list_dead_letters(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[EventDeadLetterRecord]:
        """List dead letters for a scope."""
        self._authorize(
            "event.dead_letter.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            resource_id=None,
            risk_level="low",
            approval_present=False,
        )
        return self._repository.list_dead_letters(scope=scope, status=status, limit=limit)

    def mark_resolved(
        self,
        dead_letter_id: str,
        *,
        actor_id: str | None,
        reason: str,
    ) -> EventDeadLetterRecord:
        """Mark one dead letter as resolved."""
        record = self._require_dead_letter(dead_letter_id)
        scope = _scope_from_record(record)
        self._authorize(
            "event.dead_letter.resolve",
            trace_id=record.trace_id,
            actor_id=actor_id,
            workspace_id=None,
            scope=scope,
            resource_id=dead_letter_id,
            risk_level="low",
            approval_present=True,
        )
        saved = self._repository.save_dead_letter(
            record.model_copy(
                update={
                    "status": "resolved",
                    "resolved_at": datetime.now(UTC),
                    "error": {**record.error, "resolution_reason": reason, "resolved_by": actor_id},
                }
            )
        )
        _emit(
            self._telemetry_service,
            "event_dead_letter_resolved",
            "dead_letter",
            saved.dead_letter_id,
            saved.trace_id,
            {"reason": reason},
        )
        return saved

    def replay(
        self,
        dead_letter_id: str,
        *,
        approval_present: bool = False,
    ) -> EventDispatchRecord:
        """Replay the original event through the original subscription in dry-run mode."""
        record = self._require_dead_letter(dead_letter_id)
        if record.replay_count >= self._settings.event_replay_max_count:
            raise ValueError("event_dead_letter_replay_limit_reached")
        event = self._event_repository.get(record.event_id)
        if event is None:
            raise ValueError("dead_letter_event_not_found")
        self._authorize(
            "event.dead_letter.replay",
            trace_id=record.trace_id,
            actor_id=event.actor_id,
            workspace_id=event.workspace_id,
            scope=event.security_scope or _scope_from_record(record),
            resource_id=dead_letter_id,
            risk_level="medium",
            approval_present=approval_present,
        )
        if self._router is None:
            raise RuntimeError("event_reaction_router_unavailable")
        _emit(
            self._telemetry_service,
            "event_replay_requested",
            "dead_letter",
            record.dead_letter_id,
            record.trace_id,
            {"event_id": record.event_id, "replay_count": record.replay_count + 1},
        )
        replay = self._router.dispatch(
            EventDispatchRequest(
                event=event,
                trace_id=record.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                mode="dry_run",
                owner_scope=event.security_scope or _scope_from_record(record),
                subscription_ids=[record.subscription_id] if record.subscription_id else [],
                max_actions=1,
                approval_present=approval_present,
                metadata={"dead_letter_id": dead_letter_id, "replay": True},
            )
        )
        self._repository.save_dead_letter(
            record.model_copy(
                update={
                    "status": "replayed",
                    "replay_count": record.replay_count + 1,
                    "resolved_at": datetime.now(UTC),
                }
            )
        )
        return replay

    def _require_dead_letter(self, dead_letter_id: str) -> EventDeadLetterRecord:
        record = self._repository.get_dead_letter(dead_letter_id)
        if record is None:
            raise ValueError("dead_letter_not_found")
        return record

    def _authorize(
        self,
        action_type: str,
        *,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        resource_id: str | None,
        risk_level: str,
        approval_present: bool,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="event_dead_letter",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=scope,
                context={},
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)


def _scope_from_record(record: EventDeadLetterRecord) -> list[str]:
    owner_scope = record.error.get("owner_scope")
    if isinstance(owner_scope, list):
        return [str(item) for item in owner_scope]
    return ["workspace:main"]


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    trace_id: str | None,
    payload: dict[str, object],
) -> None:
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
        from aion_brain.contracts.telemetry import (
            VisualNodeType,
            VisualTelemetryEvent,
            VisualTelemetryEventType,
        )

    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-event-router-{uuid4().hex}",
                trace_id=trace_id or f"event-router-{uuid4().hex}",
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type=cast(VisualNodeType, node_type),
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=0.8,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
