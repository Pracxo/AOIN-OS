from __future__ import annotations

import pytest

from aion_brain.contracts.effects import ExpectedEffectCreateRequest
from tests.outcome_helpers import DenyPolicy, bundle


def test_expected_effect_service_creates_effect_through_policy() -> None:
    env = bundle()
    effect = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="command_completed",
            predicate="status",
            success_criteria={"status_is": "completed"},
            owner_scope=["workspace:main"],
        )
    )

    assert effect.expected_effect_id.startswith("expected-effect-")
    assert env.policy.requests[-1].action_type == "outcome.expected_effect.create"
    assert any(
        getattr(event, "event_type", None) == "expected_effect_created"
        for event in env.telemetry.events
    )


def test_policy_deny_blocks_expected_effect_create() -> None:
    env = bundle(DenyPolicy())
    with pytest.raises(PermissionError):
        env.expected.create_expected_effect(
            ExpectedEffectCreateRequest(
                source_type="command",
                source_id="command-1",
                predicate="status",
                owner_scope=["workspace:main"],
            )
        )
