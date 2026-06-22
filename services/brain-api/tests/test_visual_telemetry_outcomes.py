from __future__ import annotations

from aion_brain.contracts.effects import ExpectedEffectCreateRequest
from tests.outcome_helpers import bundle


def test_visual_telemetry_emits_outcome_events() -> None:
    env = bundle()
    env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            predicate="status",
            owner_scope=["workspace:main"],
        )
    )

    assert any(
        getattr(event, "event_type", None) == "expected_effect_created"
        and getattr(event, "node_type", None) == "expected_effect"
        for event in env.telemetry.events
    )
