"""Shared helpers for dialogue services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)


def authorize(
    policy_adapter: object | None,
    *,
    action_type: str,
    resource_type: str,
    resource_id: str | None,
    scope: list[str],
    trace_id: str | None = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    risk_level: str = "low",
    approval_present: bool = False,
    context: dict[str, Any] | None = None,
) -> PolicyDecision:
    """Authorize through the policy adapter and fail closed on deny."""

    authorize_call = getattr(policy_adapter, "authorize", None)
    if not callable(authorize_call):
        raise PermissionError("policy_adapter_unavailable")
    decision = authorize_call(
        PolicyRequest(
            request_id=f"{action_type}-{resource_id or uuid4().hex}",
            trace_id=trace_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=approval_present,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
    )
    if not isinstance(decision, PolicyDecision):
        raise TypeError("policy adapter returned a non-PolicyDecision value")
    if not decision.allow:
        raise PermissionError(decision.reason)
    return decision


def emit_telemetry(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    trace_id: str | None,
    edge_from: str | None = None,
    edge_to: str | None = None,
    payload: dict[str, object] | None = None,
) -> None:
    """Emit a visual telemetry event when a local telemetry sink is configured."""

    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    try:
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-dialogue-{event_type}-{node_id}-{uuid4().hex}",
            trace_id=trace_id or f"dialogue-{node_id}",
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type=cast(VisualNodeType, node_type),
            node_id=node_id,
            edge_from=edge_from,
            edge_to=edge_to,
            intensity=max(0.0, min(1.0, intensity)),
            payload=payload or {},
            created_at=datetime.now(UTC),
        )
        emit(event)
    except Exception:
        return
