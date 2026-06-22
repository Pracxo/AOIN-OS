"""Autonomy visual telemetry vocabulary tests."""

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_autonomy_visual_telemetry_contracts_accept_generic_nodes() -> None:
    """Visual contracts include autonomy, delegation, and run-level semantics."""
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        trace_id="trace-1",
        event_type="autonomy_decision_recorded",
        node_type="autonomy",
        node_id="autonomy-decision-1",
        edge_from=None,
        edge_to="autonomy-decision-1",
        intensity=0.8,
        payload={"allow": True},
        created_at=datetime.now(UTC),
    )
    node = BrainVisualNode(
        node_id="delegation-1",
        node_type="delegation",
        label="Delegation",
        status="active",
        intensity=0.7,
        owner_scope=["workspace:main"],
        trace_refs=["trace-1"],
        source_refs=[],
        metadata={},
        first_seen_at=None,
        last_seen_at=None,
    )

    assert event.event_type == "autonomy_decision_recorded"
    assert node.node_type == "delegation"
