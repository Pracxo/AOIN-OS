"""Runtime config visual telemetry tests."""

from __future__ import annotations

from aion_brain.contracts.runtime_config import ConfigProfileCreateRequest
from tests.runtime_config_fakes import SCOPE, services


def test_visual_telemetry_emits_runtime_config_events() -> None:
    _, profiles, *_rest, telemetry = services()

    profiles.create_profile(
        ConfigProfileCreateRequest(
            name="telemetry",
            description="telemetry profile",
            owner_scope=SCOPE,
        )
    )

    assert any(
        getattr(event, "event_type", None) == "config_profile_created"
        for event in telemetry.events
    )
