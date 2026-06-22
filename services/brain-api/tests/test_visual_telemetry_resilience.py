"""Resilience visual telemetry contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_visual_telemetry_accepts_resilience_event_type() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-resilience-1",
        trace_id="trace-1",
        event_type="circuit_breaker_opened",
        node_type="circuit_breaker",
        node_id="breaker-1",
        edge_from=None,
        edge_to=None,
        intensity=1.0,
        payload={},
        created_at=datetime.now(UTC),
    )

    assert event.event_type == "circuit_breaker_opened"


def test_visual_contract_accepts_resilience_node_type() -> None:
    node = BrainVisualNode(
        node_id="dependency-postgres",
        node_type="dependency",
        label="Dependency",
        status="active",
        intensity=0.8,
        owner_scope=["workspace:main"],
        trace_refs=[],
        source_refs=[],
        metadata={},
        first_seen_at=None,
        last_seen_at=None,
    )

    assert node.node_type == "dependency"
