from __future__ import annotations

from aion_brain.telemetry.visual import build_operator_console_telemetry_event


def test_visual_telemetry_supports_local_session_events_and_nodes() -> None:
    event = build_operator_console_telemetry_event(
        telemetry_id="telemetry-local-session-1",
        event_type="local_session_preview_created",
        node_type="local_session_preview",
        node_id="local-session-preview-1",
        scope=["workspace:main"],
        payload={"production_session": False},
    )

    assert event.event_type == "local_session_preview_created"
    assert event.node_type == "local_session_preview"
    assert event.payload["read_only"] is True
    assert event.payload["production_auth"] is False
    assert event.payload["production_session"] is False
