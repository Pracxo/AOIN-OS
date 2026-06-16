from __future__ import annotations

from aion_brain.contracts.dialogue import DialogueTurnRequest
from tests.dialogue_helpers import FakeTelemetry, service_bundle


def test_visual_telemetry_emits_dialogue_and_response_events() -> None:
    bundle = service_bundle()
    assert isinstance(bundle.telemetry, FakeTelemetry)

    bundle.turn_service.turn(DialogueTurnRequest(message="hello", owner_scope=["workspace:main"]))

    event_types = {getattr(event, "event_type", "") for event in bundle.telemetry.events}
    assert "dialogue_turn_started" in event_types
    assert "response_composed" in event_types
    assert "dialogue_turn_completed" in event_types
