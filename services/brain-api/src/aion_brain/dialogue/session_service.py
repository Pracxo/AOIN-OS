"""Dialogue session manager."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.attention import FocusSessionCreateRequest
from aion_brain.contracts.dialogue import DialogueSession, DialogueSessionCreateRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.repository import DialogueRepository


class DialogueSessionService:
    """Create, read, list, and close generic dialogue sessions."""

    def __init__(
        self,
        repository: DialogueRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        focus_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._focus_service = focus_service

    def create_session(self, request: DialogueSessionCreateRequest) -> DialogueSession:
        """Create a dialogue session after policy authorization."""

        now = datetime.now(UTC)
        session_id = request.dialogue_session_id or f"dialogue-session-{uuid4().hex}"
        scope = request.owner_scope or ["workspace:main"]
        authorize(
            self._policy_adapter,
            action_type="dialogue.session.create",
            resource_type="dialogue_session",
            resource_id=session_id,
            scope=scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"session_type": request.session_type},
        )
        active_focus_session_id = request.active_focus_session_id or self._maybe_create_focus(
            request,
            session_id,
            scope,
        )
        session = DialogueSession(
            dialogue_session_id=session_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="active",
            session_type=request.session_type,
            title=request.title,
            owner_scope=scope,
            active_focus_session_id=active_focus_session_id,
            active_goal_id=request.active_goal_id,
            active_task_id=request.active_task_id,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            closed_at=None,
        )
        stored = self._repository.save_session(session)
        emit_telemetry(
            self._telemetry_service,
            event_type="dialogue_session_created",
            node_type="dialogue",
            node_id=stored.dialogue_session_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "workspace_id": stored.workspace_id},
        )
        return stored

    def get_session(self, dialogue_session_id: str, scope: list[str]) -> DialogueSession | None:
        """Return one visible dialogue session."""

        authorize(
            self._policy_adapter,
            action_type="dialogue.session.read",
            resource_type="dialogue_session",
            resource_id=dialogue_session_id,
            scope=scope,
            context={},
        )
        session = self._repository.get_session(dialogue_session_id)
        if session is None or not _scope_matches(session.owner_scope, scope):
            return None
        return session

    def list_sessions(
        self,
        scope: list[str],
        status: str | None = None,
        session_type: str | None = None,
        limit: int = 50,
    ) -> list[DialogueSession]:
        """List visible dialogue sessions."""

        authorize(
            self._policy_adapter,
            action_type="dialogue.session.read",
            resource_type="dialogue_session",
            resource_id=None,
            scope=scope,
            context={"status": status, "session_type": session_type},
        )
        return self._repository.list_sessions(
            scope=scope,
            status=status,
            session_type=session_type,
            limit=limit,
        )

    def close_session(
        self,
        dialogue_session_id: str,
        actor_id: str | None,
        reason: str,
    ) -> DialogueSession:
        """Close a dialogue session without deleting messages."""

        session = self._repository.get_session(dialogue_session_id)
        if session is None:
            raise ValueError("dialogue_session_not_found")
        authorize(
            self._policy_adapter,
            action_type="dialogue.session.update",
            resource_type="dialogue_session",
            resource_id=dialogue_session_id,
            scope=session.owner_scope,
            trace_id=session.trace_id,
            actor_id=actor_id,
            workspace_id=session.workspace_id,
            risk_level="low",
            context={"reason": reason},
        )
        closed = session.model_copy(
            update={
                "status": "closed",
                "updated_at": datetime.now(UTC),
                "closed_at": datetime.now(UTC),
                "metadata": {
                    **session.metadata,
                    "closed_by": actor_id,
                    "close_reason": reason,
                },
            }
        )
        stored = self._repository.save_session(closed)
        emit_telemetry(
            self._telemetry_service,
            event_type="dialogue_session_closed",
            node_type="dialogue",
            node_id=stored.dialogue_session_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "reason": reason},
        )
        return stored

    def _maybe_create_focus(
        self,
        request: DialogueSessionCreateRequest,
        session_id: str,
        scope: list[str],
    ) -> str | None:
        if request.metadata.get("create_focus") is not True:
            return None
        create_focus = getattr(self._focus_service, "create_focus_session", None)
        if not callable(create_focus):
            return None
        try:
            focus = create_focus(
                FocusSessionCreateRequest(
                    focus_session_id=None,
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    focus_type="general",
                    active_goal_id=request.active_goal_id,
                    active_task_id=request.active_task_id,
                    active_workflow_run_id=None,
                    active_trace_id=request.trace_id,
                    owner_scope=scope,
                    title=request.title,
                    description=f"Dialogue session {session_id}",
                    constraints=[],
                    metadata={"dialogue_session_id": session_id},
                )
            )
            value = getattr(focus, "focus_session_id", None)
            return str(value) if value is not None else None
        except Exception:
            return None


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))
