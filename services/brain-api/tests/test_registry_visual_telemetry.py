"""Registry visual telemetry tests."""

from __future__ import annotations

from aion_brain.contracts.telemetry import VisualTelemetryEvent


def test_registry_visual_event_types_are_contract_vocabulary() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-registry",
        trace_id="trace-registry",
        event_type="resource_indexed",
        node_type="resource",
        node_id="aion://generic/1",
        edge_from=None,
        edge_to=None,
        intensity=0.5,
        payload={},
        created_at="2026-01-01T00:00:00Z",
    )

    assert event.event_type == "resource_indexed"
