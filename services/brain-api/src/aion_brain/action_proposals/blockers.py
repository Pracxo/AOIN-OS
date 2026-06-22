"""Action blocker service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import ActionBlocker
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ActionBlockerService:
    """Manage metadata-only action blockers."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ActionBlockerService:
        return ActionBlockerService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_blocker(
        self,
        *,
        blocker_type: str,
        severity: str,
        reason: str,
        action_proposal_id: str | None = None,
        trace_id: str | None = None,
        missing_requirement: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ActionBlocker:
        """Create a blocker. This never executes or resolves the proposal."""

        blocker = ActionBlocker(
            action_blocker_id=f"action-blocker-{uuid4().hex}",
            action_proposal_id=action_proposal_id,
            trace_id=trace_id,
            blocker_type=blocker_type,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            status="open",
            reason=reason,
            missing_requirement=missing_requirement,
            source_type=source_type,
            source_id=source_id,
            metadata=dict(metadata or {}),
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_blocker", None)
        stored = save(blocker) if callable(save) else blocker
        stored = stored if isinstance(stored, ActionBlocker) else blocker
        emit_telemetry(
            self._telemetry_service,
            event_type="action_blocker_created",
            node_type="action_blocker",
            node_id=stored.action_blocker_id,
            intensity=1.0 if stored.severity in {"high", "critical"} else 0.7,
            trace_id=stored.trace_id,
            payload={"blocker_type": stored.blocker_type, "status": stored.status},
        )
        return stored

    def list_blockers(
        self,
        action_proposal_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ActionBlocker]:
        """List action blockers after policy."""

        authorize(
            self._policy_adapter,
            action_type="action_proposal.blocker.read",
            resource_type="action_blocker",
            resource_id=action_proposal_id,
            scope=_scope(self._actor_context),
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_blockers = getattr(self._repository, "list_blockers", None)
        if not callable(list_blockers):
            return []
        result = list_blockers(
            action_proposal_id=action_proposal_id,
            status=status,
            severity=severity,
            limit=limit,
        )
        return [item for item in result if isinstance(item, ActionBlocker)]

    def resolve_blocker(
        self,
        action_blocker_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ActionBlocker:
        """Resolve a blocker. Resolution does not hand off or execute."""

        authorize(
            self._policy_adapter,
            action_type="action_proposal.blocker.update",
            resource_type="action_blocker",
            resource_id=action_blocker_id,
            scope=_scope(self._actor_context),
            trace_id=self._actor_context.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        get_blocker = getattr(self._repository, "get_blocker", None)
        blocker = get_blocker(action_blocker_id) if callable(get_blocker) else None
        if not isinstance(blocker, ActionBlocker):
            raise ValueError("action_blocker_not_found")
        resolved = blocker.model_copy(
            update={
                "status": "resolved",
                "resolved_at": datetime.now(UTC),
                "metadata": {**blocker.metadata, "resolution_reason": reason},
            }
        )
        save = getattr(self._repository, "save_blocker", None)
        stored = save(resolved) if callable(save) else resolved
        stored = stored if isinstance(stored, ActionBlocker) else resolved
        emit_telemetry(
            self._telemetry_service,
            event_type="action_blocker_resolved",
            node_type="action_blocker",
            node_id=stored.action_blocker_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"status": stored.status},
        )
        return stored


def _scope(actor_context: ActorContext) -> list[str]:
    if actor_context.security_scope:
        return actor_context.security_scope
    if actor_context.workspace_id:
        return [f"workspace:{actor_context.workspace_id}"]
    return ["workspace:main"]


__all__ = ["ActionBlockerService"]
