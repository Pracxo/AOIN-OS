"""AION-181 resource-budget tests."""

from __future__ import annotations

from pathlib import Path

from test_self_improvement_shadow_activation_contracts import make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationResourceBudget,
    ShadowActivationResourceUsage,
    canonical_activation_resource_limits,
    evaluate_shadow_activation_budget,
)


def test_canonical_limits_are_exact() -> None:
    budget = ShadowActivationResourceBudget()
    for field, maximum in canonical_activation_resource_limits().items():
        assert getattr(budget, field) == maximum


def test_every_overrun_is_detected(tmp_path: Path) -> None:
    budget = make_context(tmp_path)["budget"]
    fields = [
        "activation_window_seconds",
        "runs",
        "observation_references",
        "evaluation_records",
        "failure_patterns",
        "hypotheses",
        "regression_test_proposals",
        "shadow_proposals",
        "concurrency",
        "wall_clock_seconds",
        "benchmark_cost_units",
        "output_bytes",
        "total_output_bytes",
        "output_files",
        "retention_seconds",
        "production_exposure_basis_points",
        "network_calls",
        "connector_calls",
        "provider_calls",
        "git_operations",
        "source_mutations",
        "real_pull_requests",
        "approvals_created",
        "merges",
        "runtime_promotions",
        "production_canaries",
        "deployments",
        "model_training_runs",
    ]
    for field in fields:
        usage = ShadowActivationResourceUsage(**{field: 1_000_000_000})
        decision = evaluate_shadow_activation_budget(usage, budget)
        assert decision.within_budget is False
        assert decision.fail_closed is True
