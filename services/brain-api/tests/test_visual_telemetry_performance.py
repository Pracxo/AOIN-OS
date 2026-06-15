"""Performance visual telemetry contract tests."""

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_visual_telemetry_accepts_performance_event_type() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-performance-1",
        trace_id="trace-1",
        event_type="benchmark_completed",
        node_type="benchmark",
        node_id="benchmark-run-1",
        edge_from=None,
        edge_to=None,
        intensity=0.9,
        payload={},
        created_at=datetime.now(UTC),
    )

    assert event.event_type == "benchmark_completed"


def test_visual_contract_accepts_performance_node_type() -> None:
    node = BrainVisualNode(
        node_id="performance-sample-1",
        node_type="performance",
        label="Performance sample",
        status="active",
        intensity=0.5,
        owner_scope=["workspace:main"],
        trace_refs=[],
        source_refs=[],
        metadata={},
        first_seen_at=None,
        last_seen_at=None,
    )

    assert node.node_type == "performance"
