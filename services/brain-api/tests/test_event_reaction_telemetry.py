"""Event reaction visual telemetry vocabulary tests."""

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_event_reaction_telemetry_terms_are_supported() -> None:
    """Router telemetry event and node types are part of the visual vocabulary."""
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        trace_id="trace-1",
        event_type="event_reaction_completed",
        node_type="reaction",
        node_id="action-1",
        edge_from=None,
        edge_to=None,
        intensity=0.7,
        payload={},
        created_at=datetime.now(UTC),
    )
    node = BrainVisualNode(
        node_id="dead-1",
        node_type="dead_letter",
        label="Dead letter",
        status="active",
        intensity=0.4,
        owner_scope=["workspace:main"],
    )

    assert event.event_type == "event_reaction_completed"
    assert event.node_type == "reaction"
    assert node.node_type == "dead_letter"
