"""Shared resilience helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.policy.base import PolicyAdapter


def authorize(
    policy_adapter: PolicyAdapter,
    action_type: str,
    scope: list[str],
    *,
    actor_id: str | None = None,
    resource_type: str = "resilience",
    resource_id: str | None = None,
    risk_level: str = "low",
    context: dict[str, Any] | None = None,
) -> None:
    """Authorize one generic resilience action."""
    decision = policy_adapter.authorize(
        PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=None,
            actor_id=actor_id,
            workspace_id=None,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
    )
    if not decision.allow:
        raise AIONPolicyDeniedException(decision.reason)


def emit_resilience_event(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> None:
    """Emit visual telemetry if the local telemetry service is available."""
    if telemetry_service is None:
        return
    event = VisualTelemetryEvent(
        telemetry_id=f"telemetry-{event_type}-{node_id}",
        trace_id=trace_id or node_id,
        event_type=cast(VisualTelemetryEventType, event_type),
        node_type=cast(VisualNodeType, node_type),
        node_id=node_id,
        edge_from=trace_id,
        edge_to=node_id,
        intensity=max(0.0, min(1.0, intensity)),
        payload=payload or {},
        created_at=datetime.now(UTC),
    )
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
    except Exception:
        return
