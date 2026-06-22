"""Telemetry vocabulary tests for release packaging."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_release_package_visual_telemetry_event_is_valid() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-release-package-1",
        trace_id="release-package-1",
        event_type="release_package_created",
        node_type="release_package",
        node_id="release-package-1",
        edge_from=None,
        edge_to=None,
        intensity=0.9,
        payload={"owner_scope": ["workspace:main"], "version": "0.1.0"},
        created_at=datetime.now(UTC),
    )

    assert event.event_type == "release_package_created"
    assert event.node_type == "release_package"


def test_visual_contract_accepts_release_package_node_type() -> None:
    node = BrainVisualNode(
        node_id="release-package-1",
        node_type="release_package",
        label="AION 0.1.0 package",
        status="completed",
        intensity=0.8,
        owner_scope=["workspace:main"],
        trace_refs=[],
        source_refs=[],
        metadata={},
        first_seen_at=None,
        last_seen_at=None,
    )

    assert node.node_type == "release_package"
