"""AION-178 shadow resource-budget tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_contracts import make_bundle, make_manifest, make_reference

from aion_brain.self_improvement.shadow_budget import (
    ShadowBudgetDecision,
    ShadowResourceBudget,
    ShadowResourceUsage,
    evaluate_shadow_budget,
)


def test_default_limits_are_exact() -> None:
    budget = ShadowResourceBudget()

    assert budget.maximum_observation_references == 1000
    assert budget.maximum_evaluation_records == 1000
    assert budget.maximum_failure_patterns == 100
    assert budget.maximum_hypotheses == 50
    assert budget.maximum_regression_test_proposals == 25
    assert budget.maximum_shadow_proposals == 10
    assert budget.maximum_concurrency == 4
    assert budget.maximum_wall_clock_seconds == 1800
    assert budget.maximum_benchmark_cost_units == 50
    assert budget.maximum_output_bytes == 10485760
    assert budget.maximum_operator_output_files == 20
    assert budget.network_calls == 0
    assert budget.git_operations == 0
    assert budget.source_mutations == 0
    assert budget.real_pull_requests == 0
    assert budget.runtime_promotions == 0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("observation_references", 1001),
        ("evaluation_records", 1001),
        ("failure_patterns", 101),
        ("hypotheses", 51),
        ("regression_test_proposals", 26),
        ("shadow_proposals", 11),
        ("concurrency", 5),
        ("wall_clock_seconds", 1801.0),
        ("benchmark_cost_units", 51),
        ("output_bytes", 10485761),
        ("output_files", 21),
        ("network_calls", 1),
        ("git_operations", 1),
        ("source_mutations", 1),
        ("real_pull_requests", 1),
        ("runtime_promotions", 1),
    ),
)
def test_each_budget_dimension_overrun_fails_closed(field: str, value: int | float) -> None:
    usage = ShadowResourceUsage(**{field: value})
    decision = evaluate_shadow_budget(usage, ShadowResourceBudget())
    expected_violation = {
        "observation_references": "maximum_observation_references",
        "evaluation_records": "maximum_evaluation_records",
        "failure_patterns": "maximum_failure_patterns",
        "hypotheses": "maximum_hypotheses",
        "regression_test_proposals": "maximum_regression_test_proposals",
        "shadow_proposals": "maximum_shadow_proposals",
        "concurrency": "maximum_concurrency",
        "wall_clock_seconds": "maximum_wall_clock_seconds",
        "benchmark_cost_units": "maximum_benchmark_cost_units",
        "output_bytes": "maximum_output_bytes",
        "output_files": "maximum_operator_output_files",
        "network_calls": "network_calls",
        "git_operations": "git_operations",
        "source_mutations": "source_mutations",
        "real_pull_requests": "real_pull_requests",
        "runtime_promotions": "runtime_promotions",
    }[field]

    assert decision.within_budget is False
    assert decision.run_stopped is True
    assert decision.fail_closed is True
    assert expected_violation in decision.violations


def test_negative_usage_and_quality_override_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ShadowResourceUsage(network_calls=-1)
    usage = ShadowResourceUsage(network_calls=1)
    decision = evaluate_shadow_budget(usage, ShadowResourceBudget())
    payload = decision.model_dump(mode="python")
    payload["quality_override_allowed"] = True

    with pytest.raises(ValidationError):
        ShadowBudgetDecision(**payload)


def test_budget_failure_withholds_partial_candidates() -> None:
    refs = tuple(make_reference(f"shadow-ref-{index}") for index in range(2))
    manifest = make_manifest(references=refs)
    bundle = make_bundle(
        manifest=manifest,
        snapshots=(),
        budget=ShadowResourceBudget(maximum_observation_references=1),
    )

    assert bundle.outcome == "budget_blocked"
    assert bundle.budget_failure is not None
    assert bundle.hypotheses == ()
    assert bundle.shadow_proposals == ()
    assert bundle.approval_created is False
    assert bundle.runtime_effect is False
