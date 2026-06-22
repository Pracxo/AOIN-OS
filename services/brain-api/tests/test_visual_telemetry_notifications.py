"""Visual telemetry coverage for notification center events."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent


def test_notification_visual_telemetry_event_and_node_types_are_supported() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-notification-1",
        trace_id="trace-1",
        event_type="notification_published",
        node_type="notification",
        node_id="notification-1",
        edge_from=None,
        edge_to=None,
        intensity=0.8,
        payload={"topic_key": "generic.info"},
        created_at=datetime.now(UTC),
    )
    alert = VisualTelemetryEvent(
        telemetry_id="telemetry-alert-1",
        trace_id="trace-1",
        event_type="alert_created",
        node_type="alert",
        node_id="alert-1",
        edge_from=None,
        edge_to=None,
        intensity=1.0,
        payload={"alert_type": "generic"},
        created_at=datetime.now(UTC),
    )

    assert event.event_type == "notification_published"
    assert alert.node_type == "alert"
