from __future__ import annotations

from aion_brain.telemetry.visual import build_operator_console_telemetry_event


def test_visual_telemetry_supports_local_auth_events_and_nodes() -> None:
    event = build_operator_console_telemetry_event(
        telemetry_id="telemetry-local-auth-1",
        event_type="local_auth_context_simulated",
        node_type="local_auth_context",
        node_id="local-auth-context-1",
        scope=["workspace:main"],
        payload={"production_auth": False},
    )

    assert event.event_type == "local_auth_context_simulated"
    assert event.node_type == "local_auth_context"
    assert event.payload["read_only"] is True
    assert event.payload["production_auth"] is False
