from __future__ import annotations

from aion_brain.telemetry.visual import build_operator_console_telemetry_event


def test_visual_telemetry_supports_operator_console_events() -> None:
    event = build_operator_console_telemetry_event(
        telemetry_id="telemetry-console-1",
        event_type="operator_console_view_model_created",
        node_type="operator_console_view",
        node_id="console-view-1",
        scope=["workspace:main"],
        payload={"status": "ready"},
    )

    assert event.event_type == "operator_console_view_model_created"
    assert event.node_type == "operator_console_view"
    assert event.payload["read_only"] is True
    assert event.payload["frontend_enabled"] is False
