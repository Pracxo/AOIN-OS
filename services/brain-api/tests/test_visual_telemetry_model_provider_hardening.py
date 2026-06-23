"""Visual telemetry coverage for model provider hardening events."""

from __future__ import annotations

from tests.model_provider_hardening_helpers import egress_request, services, simulation_request


def test_visual_telemetry_emits_provider_hardening_events() -> None:
    bundle = services()

    bundle["egress_guard"].preview(egress_request())  # type: ignore[attr-defined]
    bundle["simulator"].simulate(simulation_request())  # type: ignore[attr-defined]

    events = {getattr(event, "event_type", "") for event in bundle["telemetry"].events}  # type: ignore[index]
    assert "prompt_egress_preview_created" in events
    assert "model_provider_simulation_completed" in events
