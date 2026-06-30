from __future__ import annotations

from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType
from aion_brain.telemetry.visual import CONNECTOR_POLICY_TELEMETRY_EVENTS


def test_connector_policy_visual_telemetry_events_are_registered() -> None:
    events = set(CONNECTOR_POLICY_TELEMETRY_EVENTS)

    assert "connector_policy_catalog_read" in events
    assert "connector_authorization_matrix_read" in events
    assert "connector_policy_dry_run_completed" in events
    assert "connector_policy_traceability_queried" in events
    assert "connector_policy_catalog_read" in VisualTelemetryEventType.__args__
    assert "connector_policy_dry_run" in VisualNodeType.__args__

