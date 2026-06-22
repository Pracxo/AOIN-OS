"""Best-effort visual telemetry for release candidate records."""

from __future__ import annotations

from typing import Any, cast

from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType
from aion_brain.versioning.compatibility import emit_versioning_telemetry


def emit_rc_telemetry(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    scope: list[str],
    intensity: float = 0.5,
    payload: dict[str, Any] | None = None,
) -> None:
    """Emit visual telemetry without affecting RC flow."""

    emit_versioning_telemetry(
        telemetry_service,
        event_type=cast(VisualTelemetryEventType, event_type),
        node_type=cast(VisualNodeType, node_type),
        node_id=node_id,
        intensity=max(0.0, min(1.0, intensity)),
        scope=scope,
        payload=payload or {},
    )


__all__ = ["emit_rc_telemetry"]
