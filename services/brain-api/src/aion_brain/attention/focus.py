"""Focus session lifecycle service."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.attention.repository import AttentionRepository
from aion_brain.contracts.attention import (
    FocusSession,
    FocusSessionCreateRequest,
    FocusTransitionRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.policy.base import PolicyAdapter


class FocusService:
    """Manage active cognitive focus sessions."""

    def __init__(
        self,
        repository: AttentionRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_focus_session(self, request: FocusSessionCreateRequest) -> FocusSession:
        """Create an active focus session, pausing prior active focus."""
        self._authorize(
            action_type="attention.focus.create",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope,
            resource_id=request.focus_session_id,
            context={"focus_type": request.focus_type},
        )
        previous = self._repository.get_active_focus(
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope,
        )
        if previous is not None:
            paused = previous.model_copy(
                update={
                    "status": "paused",
                    "paused_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
            self._repository.save_focus_session(paused)
            self._emit_focus("focus_session_paused", paused, intensity=0.3)

        now = datetime.now(UTC)
        session = FocusSession(
            focus_session_id=request.focus_session_id or f"focus-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="active",
            focus_type=request.focus_type,
            active_goal_id=request.active_goal_id,
            active_task_id=request.active_task_id,
            active_workflow_run_id=request.active_workflow_run_id,
            active_trace_id=request.active_trace_id,
            owner_scope=request.owner_scope,
            title=request.title,
            description=request.description,
            constraints=request.constraints,
            metadata=request.metadata,
            started_at=now,
            paused_at=None,
            ended_at=None,
            created_at=now,
            updated_at=now,
        )
        stored = self._repository.save_focus_session(session)
        self._emit_focus("focus_session_started", stored, intensity=0.6)
        return stored

    def get_focus_session(self, focus_session_id: str, scope: list[str]) -> FocusSession | None:
        """Return a focus session if visible to scope."""
        self._authorize(
            action_type="attention.focus.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            resource_id=focus_session_id,
            context={},
        )
        session = self._repository.get_focus_session(focus_session_id)
        if session is None or not _scope_matches(session.owner_scope, scope):
            return None
        return session

    def get_active_focus(
        self,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
    ) -> FocusSession | None:
        """Return the newest active focus for an actor/workspace."""
        self._authorize(
            action_type="attention.focus.read",
            trace_id=None,
            actor_id=actor_id,
            workspace_id=workspace_id,
            scope=scope,
            resource_id=None,
            context={"operation": "active_focus"},
        )
        return self._repository.get_active_focus(
            actor_id=actor_id,
            workspace_id=workspace_id,
            scope=scope,
        )

    def list_focus_sessions(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[FocusSession]:
        """List focus sessions visible to scope."""
        self._authorize(
            action_type="attention.focus.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            resource_id=None,
            context={"operation": "list_focus"},
        )
        return self._repository.list_focus_sessions(scope=scope, status=status, limit=limit)

    def transition_focus(self, request: FocusTransitionRequest) -> FocusSession:
        """Transition focus status through allowed lifecycle edges."""
        session = self._repository.get_focus_session(request.focus_session_id)
        if session is None:
            raise ValueError("focus_session_not_found")
        self._authorize(
            action_type="attention.focus.update",
            trace_id=session.trace_id,
            actor_id=request.actor_id or session.actor_id,
            workspace_id=session.workspace_id,
            scope=session.owner_scope,
            resource_id=session.focus_session_id,
            context={"to_status": request.to_status, "reason": request.reason},
        )
        if (session.status, request.to_status) not in {
            ("active", "paused"),
            ("active", "ended"),
            ("paused", "active"),
            ("paused", "ended"),
        }:
            raise ValueError("invalid_focus_transition")
        now = datetime.now(UTC)
        updates: dict[str, object] = {
            "status": request.to_status,
            "updated_at": now,
            "metadata": {
                **session.metadata,
                **request.metadata,
                "transition_reason": request.reason,
            },
        }
        if request.to_status == "paused":
            updates["paused_at"] = now
        if request.to_status == "active":
            updates["paused_at"] = None
            updates["started_at"] = session.started_at or now
        if request.to_status == "ended":
            updates["ended_at"] = now
        stored = self._repository.save_focus_session(session.model_copy(update=updates))
        self._emit_focus(
            _event_type_for_transition(request.to_status),
            stored,
            intensity=_focus_intensity(request.to_status),
        )
        return stored

    def _authorize(
        self,
        *,
        action_type: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        resource_id: str | None,
        context: dict[str, object],
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="focus_session",
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _emit_focus(
        self,
        event_type: str,
        session: FocusSession,
        *,
        intensity: float,
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{session.focus_session_id}-{event_type}",
            trace_id=session.trace_id or session.focus_session_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="focus",
            node_id=session.focus_session_id,
            edge_from=None,
            edge_to=session.active_trace_id,
            intensity=intensity,
            payload={
                "focus_session_id": session.focus_session_id,
                "focus_type": session.focus_type,
                "owner_scope": session.owner_scope,
                "workspace_id": session.workspace_id,
            },
            created_at=datetime.now(UTC),
        )
        _emit(self._telemetry_service, event)


def _event_type_for_transition(status: str) -> str:
    if status == "paused":
        return "focus_session_paused"
    if status == "active":
        return "focus_session_resumed"
    return "focus_session_ended"


def _focus_intensity(status: str) -> float:
    if status == "paused":
        return 0.3
    if status == "active":
        return 0.7
    return 0.2


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))


def _emit(telemetry_service: object, event: VisualTelemetryEvent) -> None:
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
            return
        save = getattr(telemetry_service, "save_visual_telemetry", None)
        if callable(save):
            save(event.trace_id, [event])
    except Exception:
        return
