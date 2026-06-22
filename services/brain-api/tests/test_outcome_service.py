from __future__ import annotations

from aion_brain.contracts.effects import ExpectedEffectCreateRequest, ObservedEffectCreateRequest
from aion_brain.contracts.outcomes import OutcomeCreateRequest
from tests.outcome_helpers import bundle


def test_outcome_service_creates_unknown_outcome_without_expected_effects() -> None:
    env = bundle()
    outcome = env.outcomes.create_outcome(
        OutcomeCreateRequest(
            source_type="command",
            source_id="command-1",
            outcome_type="command",
            title="Command completed",
            summary="Completion observed only.",
            owner_scope=["workspace:main"],
        )
    )

    assert outcome.status == "unknown"


def test_outcome_service_creates_verified_when_required_effects_match() -> None:
    env = bundle()
    expected = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="command_completed",
            predicate="status",
            success_criteria={"status_is": "completed"},
            owner_scope=["workspace:main"],
        )
    )
    observed = env.observed.create_observed_effect(
        ObservedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="command_completed",
            predicate="status",
            observed_value={"status": "completed"},
            observation_source_type="command",
            observation_source_id="command-1",
            owner_scope=["workspace:main"],
        )
    )
    outcome = env.outcomes.create_outcome(
        OutcomeCreateRequest(
            source_type="command",
            source_id="command-1",
            outcome_type="command",
            title="Command outcome",
            summary="Expected effect matched.",
            owner_scope=["workspace:main"],
            expected_effects=[expected.expected_effect_id],
            observed_effects=[observed.observed_effect_id],
        )
    )

    assert outcome.status == "verified"
    assert outcome.score >= 0.75


def test_outcome_service_creates_partial_when_optional_effect_missing() -> None:
    env = bundle()
    required = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="command_completed",
            predicate="status",
            success_criteria={"status_is": "completed"},
            owner_scope=["workspace:main"],
        )
    )
    optional = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="record_created",
            predicate="record",
            required=False,
            success_criteria={"exists": True},
            owner_scope=["workspace:main"],
        )
    )
    observed = env.observed.create_observed_effect(
        ObservedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="command_completed",
            predicate="status",
            observed_value={"status": "completed"},
            observation_source_type="command",
            observation_source_id="command-1",
            owner_scope=["workspace:main"],
        )
    )
    outcome = env.outcomes.create_outcome(
        OutcomeCreateRequest(
            source_type="command",
            source_id="command-1",
            outcome_type="command",
            title="Command outcome",
            summary="Optional effect missing.",
            owner_scope=["workspace:main"],
            expected_effects=[required.expected_effect_id, optional.expected_effect_id],
            observed_effects=[observed.observed_effect_id],
        )
    )

    assert outcome.status == "partial"
