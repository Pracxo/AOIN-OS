"""AION-178 shadow failure-pattern mining tests."""

from __future__ import annotations

from test_self_improvement_shadow_contracts import (
    NOW,
    make_metric,
    make_observation,
    make_reference,
)

from aion_brain.self_improvement.shadow_pipeline import mine_shadow_failure_patterns


def test_single_observation_produces_no_repeated_pattern() -> None:
    observation = make_observation(repeated_count=1)

    assert mine_shadow_failure_patterns((observation,), maximum_patterns=100, created_at=NOW) == ()


def test_repeated_observation_produces_one_pattern() -> None:
    observation = make_observation(repeated_count=2)
    patterns = mine_shadow_failure_patterns((observation,), maximum_patterns=100, created_at=NOW)

    assert len(patterns) == 1
    assert patterns[0].frequency == 2
    assert patterns[0].severity == "low"
    assert patterns[0].review_state == "shadow_pattern_detected"


def test_duplicate_observations_do_not_inflate_beyond_validated_repetition() -> None:
    reference = make_reference(repeated_count=2)
    observation = make_observation("shadow-observation-1", reference=reference, repeated_count=2)

    pattern = mine_shadow_failure_patterns(
        (observation, observation),
        maximum_patterns=100,
        created_at=NOW,
    )[0]

    assert pattern.frequency == 2


def test_pattern_sorting_and_maximum_count_are_deterministic() -> None:
    retrieval = make_observation("shadow-observation-1", repeated_count=4)
    regression = make_observation(
        "shadow-observation-2",
        metric=make_metric(
            metric_name="regression_count",
            current_value=2.0,
            baseline_value=0.0,
            target_value=0.0,
            higher_is_better=False,
        ),
        repeated_count=3,
    )

    patterns = mine_shadow_failure_patterns(
        (retrieval, regression),
        maximum_patterns=1,
        created_at=NOW,
    )

    assert len(patterns) == 1
    assert patterns[0].severity == "high"
