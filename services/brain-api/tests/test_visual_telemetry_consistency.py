"""Visual telemetry consistency vocabulary tests."""

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent


def test_visual_telemetry_emits_command_idempotency_outbox_inbox_lease_consistency_events() -> None:
    """New consistency event and node types are accepted."""
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        trace_id="trace-1",
        event_type="command_created",
        node_type="command",
        node_id="command-1",
        edge_from=None,
        edge_to="command-1",
        intensity=0.5,
        payload={},
        created_at=datetime.now(UTC),
    )

    assert event.event_type == "command_created"
    assert event.node_type == "command"
