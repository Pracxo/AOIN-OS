"""Telemetry vocabulary tests for local backups."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode


def test_backup_visual_telemetry_event_is_valid() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-backup-1",
        trace_id="backup-1",
        event_type="backup_completed",
        node_type="backup",
        node_id="backup-1",
        edge_from=None,
        edge_to=None,
        intensity=0.9,
        payload={"owner_scope": ["workspace:main"]},
        created_at=datetime.now(UTC),
    )

    assert event.event_type == "backup_completed"
    assert event.node_type == "backup"


def test_visual_contract_accepts_restore_preview_node_type() -> None:
    node = BrainVisualNode(
        node_id="restore-preview-1",
        node_type="restore_preview",
        label="Restore preview",
        status="completed",
        intensity=0.8,
        owner_scope=["workspace:main"],
        trace_refs=[],
        source_refs=[],
        metadata={},
        first_seen_at=None,
        last_seen_at=None,
    )

    assert node.node_type == "restore_preview"
