"""Scenario visual telemetry vocabulary tests."""

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent


def test_visual_telemetry_accepts_scenario_and_release_events() -> None:
    scenario = VisualTelemetryEvent(
        telemetry_id="telemetry-1",
        trace_id="trace-1",
        event_type="scenario_completed",
        node_type="scenario",
        node_id="scenario-run-1",
        edge_from=None,
        edge_to=None,
        intensity=0.9,
        payload={},
        created_at=datetime.now(UTC),
    )
    baseline = VisualTelemetryEvent(
        telemetry_id="telemetry-2",
        trace_id="trace-2",
        event_type="release_baseline_completed",
        node_type="release_baseline",
        node_id="baseline-1",
        edge_from=None,
        edge_to=None,
        intensity=0.9,
        payload={},
        created_at=datetime.now(UTC),
    )

    assert scenario.event_type == "scenario_completed"
    assert baseline.node_type == "release_baseline"
