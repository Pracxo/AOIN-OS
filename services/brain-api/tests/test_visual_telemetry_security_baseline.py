"""Security visual telemetry tests."""

from __future__ import annotations

from aion_brain.contracts.telemetry import VisualTelemetryEvent


def test_visual_telemetry_accepts_security_events() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-security-1",
        trace_id="security-scan-1",
        event_type="security_scan_started",
        node_type="security",
        node_id="security-scan-1",
        edge_from=None,
        edge_to=None,
        intensity=0.5,
        payload={},
        created_at="2026-01-01T00:00:00Z",
    )

    assert event.event_type == "security_scan_started"
