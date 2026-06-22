from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_visual_telemetry_accepts_explanation_event_and_node_types() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        event_type="explanation_created",
        node_type="explanation",
        node_id="explanation-1",
        edge_from=None,
        edge_to=None,
        trace_id="trace-1",
        intensity=0.7,
        payload={"owner_scope": ["workspace:main"]},
        created_at=datetime.now(UTC),
    )
    node = BrainVisualNode(
        node_id="why-not-1",
        node_type="why_not",
        label="Why not",
        status="active",
        intensity=0.8,
        owner_scope=["workspace:main"],
        trace_refs=["trace-1"],
        source_refs=[],
        metadata={},
    )

    assert event.event_type == "explanation_created"
    assert node.node_type == "why_not"
