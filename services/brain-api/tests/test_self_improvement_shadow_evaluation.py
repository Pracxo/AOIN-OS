"""AION-178 shadow evaluation tests."""

from __future__ import annotations

from test_self_improvement_shadow_contracts import NOW, make_metric, make_observation

from aion_brain.self_improvement.shadow_mode import (
    build_shadow_evaluation_summary,
    evaluate_shadow_metrics,
)


def test_metric_drift_is_deterministic_and_weakest_metric_is_selected() -> None:
    retrieval = make_observation(
        "shadow-observation-1",
        metric=make_metric(current_value=0.4, baseline_value=0.7, target_value=0.8),
    )
    planning = make_observation(
        "shadow-observation-2",
        metric=make_metric(
            metric_name="plan_success",
            current_value=0.6,
            baseline_value=0.6,
            target_value=0.7,
        ),
    )

    drifts = evaluate_shadow_metrics((planning, retrieval))
    summary = build_shadow_evaluation_summary(
        evaluation_id="shadow-evaluation-1",
        observations=(planning, retrieval),
        benchmark_cost_units=2,
        created_at=NOW,
    )

    assert tuple(item.metric_name for item in drifts) == ("retrieval_precision", "plan_success")
    assert summary.weakest_metric == "retrieval_precision"
    assert summary.target_miss_count == 2
    assert summary.regression_count == 1
    assert summary.benchmark_cost_units == 2
    assert summary.runtime_effect is False


def test_policy_violation_count_is_accounted() -> None:
    observation = make_observation(
        metric=make_metric(
            metric_name="policy_violation_count",
            current_value=2.0,
            baseline_value=0.0,
            target_value=0.0,
            higher_is_better=False,
        ),
    )
    summary = build_shadow_evaluation_summary(
        evaluation_id="shadow-evaluation-1",
        observations=(observation,),
        benchmark_cost_units=0,
        created_at=NOW,
    )

    assert summary.policy_violation_count == 2
    assert summary.source_modified is False
