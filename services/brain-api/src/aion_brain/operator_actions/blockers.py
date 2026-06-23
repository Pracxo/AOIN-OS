"""Governed operator action blocker service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.operator_actions import OperatorActionBlocker
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class OperatorActionBlockerService:
    """Manage operator action blockers without enabling execution."""

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

    def with_actor_context(self, actor_context: ActorContext) -> OperatorActionBlockerService:
        return OperatorActionBlockerService(
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
        recommended_action: str,
        operator_action_request_id: str | None = None,
        trace_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OperatorActionBlocker:
        blocker = OperatorActionBlocker(
            operator_action_blocker_id=f"operator-action-blocker-{uuid4().hex}",
            trace_id=trace_id,
            operator_action_request_id=operator_action_request_id,
            blocker_type=blocker_type,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            status="open",
            reason=reason,
            recommended_action=recommended_action,
            source_type=source_type,
            source_id=source_id,
            metadata=dict(metadata or {}),
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_blocker", None)
        stored = save(blocker) if callable(save) else blocker
        stored = stored if isinstance(stored, OperatorActionBlocker) else blocker
        emit_telemetry(
            self._telemetry_service,
            event_type="operator_action_blocker_created",
            node_type="operator_action_blocker",
            node_id=stored.operator_action_blocker_id,
            intensity=1.0 if stored.severity in {"high", "critical"} else 0.7,
            trace_id=stored.trace_id,
            payload={
                "blocker_type": stored.blocker_type,
                "status": stored.status,
                "operator_action_request_id": stored.operator_action_request_id,
            },
        )
        return stored

    def list_blockers(
        self,
        scope: list[str],
        operator_action_request_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionBlocker]:
        authorize(
            self._policy_adapter,
            action_type="operator_action.blocker.read",
            resource_type="operator_action_blocker",
            resource_id=operator_action_request_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_blockers = getattr(self._repository, "list_blockers", None)
        if not callable(list_blockers):
            return []
        result = list_blockers(
            scope=scope,
            operator_action_request_id=operator_action_request_id,
            status=status,
            severity=severity,
            limit=limit,
        )
        return [item for item in result if isinstance(item, OperatorActionBlocker)]

    def dismiss_blocker(
        self,
        operator_action_blocker_id: str,
        actor_id: str | None,
        reason: str,
    ) -> OperatorActionBlocker:
        authorize(
            self._policy_adapter,
            action_type="operator_action.blocker.update",
            resource_type="operator_action_blocker",
            resource_id=operator_action_blocker_id,
            scope=_scope(self._actor_context),
            trace_id=self._actor_context.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason, "does_not_enable_execution": True},
        )
        get_blocker = getattr(self._repository, "get_blocker", None)
        blocker = get_blocker(operator_action_blocker_id) if callable(get_blocker) else None
        if not isinstance(blocker, OperatorActionBlocker):
            raise ValueError("operator_action_blocker_not_found")
        dismissed = blocker.model_copy(
            update={
                "status": "dismissed",
                "dismissed_at": datetime.now(UTC),
                "metadata": {
                    **blocker.metadata,
                    "dismiss_reason": reason,
                    "dismissed_by": actor_id or self._actor_context.actor_id,
                    "execution_allowed": False,
                },
            }
        )
        save = getattr(self._repository, "save_blocker", None)
        stored = save(dismissed) if callable(save) else dismissed
        stored = stored if isinstance(stored, OperatorActionBlocker) else dismissed
        emit_telemetry(
            self._telemetry_service,
            event_type="operator_action_blocker_dismissed",
            node_type="operator_action_blocker",
            node_id=stored.operator_action_blocker_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "execution_allowed": False},
        )
        return stored


def _scope(actor_context: ActorContext) -> list[str]:
    if actor_context.security_scope:
        return actor_context.security_scope
    if actor_context.workspace_id:
        return [f"workspace:{actor_context.workspace_id}"]
    return ["workspace:main"]


__all__ = ["OperatorActionBlockerService"]
