"""Visual telemetry vocabulary tests for Contract Registry."""

from __future__ import annotations

from typing import get_args

from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType
from aion_brain.contracts.visual import BrainVisualNodeType


def test_visual_telemetry_includes_contract_registry_events_and_nodes() -> None:
    event_types = set(get_args(VisualTelemetryEventType))
    telemetry_node_types = set(get_args(VisualNodeType))
    visual_node_types = set(get_args(BrainVisualNodeType))

    assert {
        "contract_indexed",
        "interface_indexed",
        "contract_snapshot_created",
        "compatibility_scan_completed",
        "interface_drift_detected",
        "migration_note_created",
        "contract_registry_report_created",
    }.issubset(event_types)
    assert {"contract_snapshot", "compatibility_scan", "interface_drift"}.issubset(
        telemetry_node_types
    )
    assert {"contract_snapshot", "compatibility_scan", "interface_drift"}.issubset(
        visual_node_types
    )
