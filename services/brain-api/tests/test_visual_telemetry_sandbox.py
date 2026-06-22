"""Visual telemetry vocabulary tests for sandbox control-plane events."""

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent


def test_visual_telemetry_accepts_sandbox_secret_connector_events() -> None:
    events = [
        VisualTelemetryEvent(
            telemetry_id="telemetry-sandbox",
            trace_id="trace-1",
            event_type="sandbox_profile_created",
            node_type="sandbox",
            node_id="sandbox-profile-1",
            edge_from=None,
            edge_to="sandbox-profile-1",
            intensity=0.5,
            payload={},
            created_at=datetime.now(UTC),
        ),
        VisualTelemetryEvent(
            telemetry_id="telemetry-secret",
            trace_id="trace-1",
            event_type="secret_ref_created",
            node_type="secret_ref",
            node_id="secret-ref-1",
            edge_from=None,
            edge_to="secret-ref-1",
            intensity=0.5,
            payload={},
            created_at=datetime.now(UTC),
        ),
        VisualTelemetryEvent(
            telemetry_id="telemetry-connector",
            trace_id="trace-1",
            event_type="connector_created",
            node_type="connector",
            node_id="connector-1",
            edge_from=None,
            edge_to="connector-1",
            intensity=0.5,
            payload={},
            created_at=datetime.now(UTC),
        ),
    ]

    assert [event.node_type for event in events] == ["sandbox", "secret_ref", "connector"]
