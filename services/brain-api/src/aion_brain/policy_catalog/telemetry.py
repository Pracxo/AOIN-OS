"""Visual telemetry helpers for policy catalog services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.telemetry import VisualTelemetryEvent


def emit_policy_telemetry(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, Any],
) -> None:
    """Persist or emit one policy visual telemetry event when possible."""
    event = VisualTelemetryEvent(
        telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
        trace_id=node_id,
        event_type=cast(Any, event_type),
        node_type=cast(Any, node_type),
        node_id=node_id,
        edge_from=None,
        edge_to=node_id,
        intensity=intensity,
        payload=payload,
        created_at=datetime.now(UTC),
    )
    save = getattr(telemetry_service, "save_visual_telemetry", None)
    emit = getattr(telemetry_service, "emit", None)
    try:
        if callable(save):
            save(node_id, [event])
        elif callable(emit):
            emit(event)
    except Exception:
        return
