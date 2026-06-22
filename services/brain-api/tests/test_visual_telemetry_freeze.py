"""Telemetry vocabulary tests for versioning and freeze events."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_versioning_visual_telemetry_events_are_valid() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        trace_id="freeze-1",
        event_type="freeze_gate_completed",
        node_type="freeze",
        node_id="freeze-1",
        edge_from=None,
        edge_to=None,
        intensity=0.9,
        payload={"owner_scope": ["workspace:main"]},
        created_at=datetime.now(UTC),
    )

    assert event.event_type == "freeze_gate_completed"
    assert event.node_type == "freeze"


def test_visual_contract_accepts_version_node_type() -> None:
    node = BrainVisualNode(
        node_id="version-0.1.0",
        node_type="version",
        label="0.1.0",
        status="completed",
        intensity=0.8,
        owner_scope=["workspace:main"],
        trace_refs=[],
        source_refs=[],
        metadata={},
        first_seen_at=None,
        last_seen_at=None,
    )

    assert node.node_type == "version"
