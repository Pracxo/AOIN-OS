"""AION-178 shadow hypothesis generation tests."""

from __future__ import annotations

from test_self_improvement_shadow_contracts import NOW, make_metric, make_observation

from aion_brain.self_improvement.shadow_pipeline import (
    generate_shadow_hypotheses,
    mine_shadow_failure_patterns,
)


def test_hypotheses_are_template_based_and_bounded() -> None:
    pattern = mine_shadow_failure_patterns(
        (make_observation(repeated_count=2),),
        maximum_patterns=100,
        created_at=NOW,
    )[0]

    hypothesis = generate_shadow_hypotheses((pattern,), maximum_hypotheses=1, created_at=NOW)[0]

    assert hypothesis.change_type == "retrieval_ranking_candidate"
    assert hypothesis.target_metric == "retrieval_precision"
    assert hypothesis.target_direction == "increase"
    assert 0.0 <= hypothesis.target_delta <= 1.0
    assert hypothesis.review_state == "shadow_hypothesis_generated"


def test_policy_hypothesis_requires_separate_authorization() -> None:
    policy = make_observation(
        metric=make_metric(
            metric_name="policy_violation_count",
            current_value=2.0,
            baseline_value=0.0,
            target_value=0.0,
            higher_is_better=False,
        ),
        repeated_count=2,
    )
    pattern = mine_shadow_failure_patterns((policy,), maximum_patterns=100, created_at=NOW)[0]
    hypothesis = generate_shadow_hypotheses((pattern,), maximum_hypotheses=50, created_at=NOW)[0]

    assert hypothesis.change_type == "governance_review"
    assert hypothesis.requires_separate_authorization is True


def test_hypothesis_maximum_count_is_enforced() -> None:
    patterns = mine_shadow_failure_patterns(
        tuple(
            make_observation(f"shadow-observation-{index}", repeated_count=2)
            for index in range(3)
        ),
        maximum_patterns=100,
        created_at=NOW,
    )

    assert len(generate_shadow_hypotheses(patterns, maximum_hypotheses=1, created_at=NOW)) == 1
