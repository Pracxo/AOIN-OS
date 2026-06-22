from __future__ import annotations

from aion_brain.contracts.effects import ExpectedEffectCreateRequest, ObservedEffectCreateRequest
from aion_brain.contracts.outcomes import EffectVerificationRequest, OutcomeCreateRequest
from tests.outcome_helpers import bundle


def test_effect_verifier_matches_equals_success_criteria() -> None:
    env = bundle()
    expected = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="generic",
            predicate="value",
            expected_value={"value": 3},
            success_criteria={"equals": {"value": 3}},
            owner_scope=["workspace:main"],
        )
    )
    observed = env.observed.create_observed_effect(
        ObservedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            effect_type="generic",
            predicate="value",
            observed_value={"value": 3},
            observation_source_type="command",
            observation_source_id="command-1",
            owner_scope=["workspace:main"],
        )
    )

    run = env.verifier.verify(
        EffectVerificationRequest(
            owner_scope=["workspace:main"],
            expected_effect_ids=[expected.expected_effect_id],
            observed_effect_ids=[observed.observed_effect_id],
            collect_observed_effects=False,
        )
    )

    assert run.status == "dry_run"
    assert run.matched_effects


def test_effect_verifier_matches_exists_success_criteria() -> None:
    env = bundle()
    expected = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            predicate="record",
            success_criteria={"exists": True},
            owner_scope=["workspace:main"],
        )
    )
    observed = env.observed.create_observed_effect(
        ObservedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            predicate="record",
            observed_value={"id": "record-1"},
            observation_source_type="command",
            observation_source_id="command-1",
            owner_scope=["workspace:main"],
        )
    )
    run = env.verifier.verify(
        EffectVerificationRequest(
            owner_scope=["workspace:main"],
            expected_effect_ids=[expected.expected_effect_id],
            observed_effect_ids=[observed.observed_effect_id],
            collect_observed_effects=False,
        )
    )

    assert run.score > 0


def test_effect_verifier_detects_missing_required_effect() -> None:
    env = bundle()
    expected = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            predicate="status",
            owner_scope=["workspace:main"],
        )
    )

    run = env.verifier.verify(
        EffectVerificationRequest(
            owner_scope=["workspace:main"],
            expected_effect_ids=[expected.expected_effect_id],
            collect_observed_effects=False,
        )
    )

    assert run.status == "failed"
    assert run.missing_effects


def test_effect_verifier_detects_unexpected_observed_effect() -> None:
    env = bundle()
    expected = env.expected.create_expected_effect(
        ExpectedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            predicate="status",
            owner_scope=["workspace:main"],
        )
    )
    observed = env.observed.create_observed_effect(
        ObservedEffectCreateRequest(
            source_type="command",
            source_id="command-1",
            predicate="other",
            observed_value={"status": "other"},
            observation_source_type="command",
            observation_source_id="command-1",
            owner_scope=["workspace:main"],
        )
    )

    run = env.verifier.verify(
        EffectVerificationRequest(
            owner_scope=["workspace:main"],
            expected_effect_ids=[expected.expected_effect_id],
            observed_effect_ids=[observed.observed_effect_id],
            collect_observed_effects=False,
        )
    )

    assert run.unexpected_effects


def test_effect_verifier_dry_run_does_not_update_outcome_record() -> None:
    env = bundle()
    outcome = env.outcomes.create_outcome(
        OutcomeCreateRequest(
            source_type="command",
            source_id="command-1",
            outcome_type="command",
            title="Outcome",
            summary="Unknown.",
            owner_scope=["workspace:main"],
        )
    )
    env.verifier.verify(
        EffectVerificationRequest(
            outcome_id=outcome.outcome_id,
            owner_scope=["workspace:main"],
            collect_observed_effects=False,
        )
    )

    assert env.repository.get_outcome(outcome.outcome_id).status == "unknown"  # type: ignore[union-attr]


def test_effect_verifier_controlled_updates_outcome_record_only() -> None:
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
            title="Outcome",
            summary="Ready.",
            owner_scope=["workspace:main"],
            expected_effects=[expected.expected_effect_id],
            observed_effects=[observed.observed_effect_id],
        )
    )

    run = env.verifier.verify(
        EffectVerificationRequest(
            outcome_id=outcome.outcome_id,
            mode="controlled",
            owner_scope=["workspace:main"],
            collect_observed_effects=False,
        )
    )

    assert run.result["mutated_source_records"] is False
    assert env.repository.get_outcome(outcome.outcome_id).status == "verified"  # type: ignore[union-attr]
