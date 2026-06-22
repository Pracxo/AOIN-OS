"""Interrupt routing for AION attention control."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.attention.repository import AttentionRepository
from aion_brain.config import Settings
from aion_brain.contracts.attention import (
    InterruptCreateRequest,
    InterruptDecisionRequest,
    InterruptRecord,
    InterruptStatus,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.policy.base import PolicyAdapter

_STATUS_BY_DECISION: dict[str, InterruptStatus] = {
    "accept": "accepted",
    "defer": "deferred",
    "dismiss": "dismissed",
    "resolve": "resolved",
}
_EVENT_BY_STATUS = {
    "accepted": "interrupt_accepted",
    "deferred": "interrupt_deferred",
    "dismissed": "interrupt_dismissed",
    "resolved": "interrupt_resolved",
}
_RISK_VALUES = {
    "low": 0.20,
    "medium": 0.45,
    "high": 0.75,
    "critical": 0.95,
}


class InterruptRouter:
    """Persist and decide generic attention interrupts."""

    def __init__(
        self,
        repository: AttentionRepository,
        policy_adapter: PolicyAdapter,
        *,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._settings = settings
        self._telemetry_service = telemetry_service

    def create_interrupt(self, request: InterruptCreateRequest) -> InterruptRecord:
        """Create a pending interrupt."""
        self._authorize(
            action_type="interrupt.create",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope,
            resource_id=request.interrupt_id,
            context={"interrupt_type": request.interrupt_type},
        )
        priority = _priority_from_payload(request.payload, request.metadata)
        interrupt = InterruptRecord(
            interrupt_id=request.interrupt_id or f"interrupt-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            focus_session_id=request.focus_session_id,
            interrupt_type=request.interrupt_type,
            source_type=request.source_type,
            source_id=request.source_id,
            status="pending",
            priority_score=priority,
            payload=request.payload,
            decision={"status": "pending", "metadata": request.metadata},
            created_at=datetime.now(UTC),
            resolved_at=None,
        )
        stored = self._repository.save_interrupt(interrupt)
        self._emit_interrupt("interrupt_created", stored, stored.priority_score)
        return stored

    def list_interrupts(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[InterruptRecord]:
        """List interrupts."""
        self._authorize(
            action_type="interrupt.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            resource_id=None,
            context={"operation": "list_interrupts"},
        )
        return self._repository.list_interrupts(scope=scope, status=status, limit=limit)

    def decide_interrupt(self, request: InterruptDecisionRequest) -> InterruptRecord:
        """Accept, defer, dismiss, or resolve an interrupt."""
        interrupt = self._repository.get_interrupt(request.interrupt_id)
        if interrupt is None:
            raise ValueError("interrupt_not_found")
        self._authorize(
            action_type="interrupt.decide",
            trace_id=interrupt.trace_id,
            actor_id=request.actor_id or interrupt.actor_id,
            workspace_id=interrupt.workspace_id,
            scope=_scope_from_interrupt(interrupt),
            resource_id=interrupt.interrupt_id,
            context={"decision": request.decision, "reason": request.reason},
        )
        status = _STATUS_BY_DECISION[request.decision]
        stored = self._repository.save_interrupt(
            interrupt.model_copy(
                update={
                    "status": status,
                    "decision": {
                        "decision": request.decision,
                        "reason": request.reason,
                        "actor_id": request.actor_id,
                        "metadata": request.metadata,
                    },
                    "resolved_at": datetime.now(UTC) if status == "resolved" else None,
                }
            )
        )
        self._emit_interrupt(_EVENT_BY_STATUS[status], stored, stored.priority_score)
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
                resource_type="interrupt",
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

    def _emit_interrupt(
        self,
        event_type: str,
        interrupt: InterruptRecord,
        intensity: float,
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{interrupt.interrupt_id}-{event_type}",
            trace_id=interrupt.trace_id or interrupt.interrupt_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="interrupt",
            node_id=interrupt.interrupt_id,
            edge_from=None,
            edge_to=interrupt.focus_session_id,
            intensity=max(0.0, min(1.0, intensity)),
            payload={
                "interrupt_type": interrupt.interrupt_type,
                "status": interrupt.status,
                "priority_score": interrupt.priority_score,
            },
            created_at=datetime.now(UTC),
        )
        _emit(self._telemetry_service, event)


def _priority_from_payload(payload: dict[str, object], metadata: dict[str, object]) -> float:
    score = 0.5
    for key in ("priority_score", "urgency", "importance"):
        value = payload.get(key, metadata.get(key))
        if isinstance(value, int | float):
            score = max(score, float(value))
    risk = payload.get("risk_level", metadata.get("risk_level"))
    if isinstance(risk, str):
        score = max(score, _RISK_VALUES.get(risk, 0.5))
    return max(0.0, min(1.0, score))


def _scope_from_interrupt(interrupt: InterruptRecord) -> list[str]:
    scope = interrupt.payload.get("owner_scope")
    if isinstance(scope, list) and all(isinstance(item, str) for item in scope):
        return list(scope)
    return ["workspace:main"]


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
