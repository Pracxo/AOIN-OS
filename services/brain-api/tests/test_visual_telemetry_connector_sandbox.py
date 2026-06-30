from __future__ import annotations

from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType
from aion_brain.telemetry.visual import CONNECTOR_SANDBOX_TELEMETRY_EVENTS


def test_connector_sandbox_visual_telemetry_events_are_registered() -> None:
    events = set(CONNECTOR_SANDBOX_TELEMETRY_EVENTS)

    assert "connector_sandbox_boundary_read" in events
    assert "connector_sandbox_capability_rules_read" in events
    assert "connector_sandbox_readiness_checked" in events
    assert "connector_sandbox_boundary_read" in VisualTelemetryEventType.__args__
    assert "connector_sandbox_readiness" in VisualNodeType.__args__
