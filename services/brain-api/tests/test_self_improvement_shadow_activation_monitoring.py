"""AION-181 monitoring tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    SHADOW_ACTIVATION_MONITORING_METRICS,
    ShadowActivationHealthSnapshot,
    ShadowActivationMonitoringPlan,
    evaluate_shadow_activation_health,
)


def test_monitoring_requires_exact_metric_coverage(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["monitoring_plan"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    payload["required_metric_names"] = SHADOW_ACTIVATION_MONITORING_METRICS[:-1]
    with pytest.raises(ValidationError):
        ShadowActivationMonitoringPlan(**payload)


def test_monitoring_triggers_required_deactivation_conditions(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    for field in (
        "network_call_count",
        "git_operation_count",
        "source_mutation_count",
        "real_pr_count",
        "approval_creation_count",
        "runtime_promotion_count",
        "runtime_influence_count",
        "output_boundary_failure_count",
        "redaction_failure_count",
        "fingerprint_mismatch_count",
        "budget_violation_count",
    ):
        snapshot = ShadowActivationHealthSnapshot(
            activation_candidate_id=ctx["candidate"].activation_candidate_id,
            observed_at=NOW,
            **{field: 1},
        )
        decision = evaluate_shadow_activation_health(
            snapshot,
            ctx["monitoring_plan"],
            activation_window_end=ctx["request"].activation_window_end,
            maximum_runs=ctx["request"].maximum_runs,
            now=NOW,
        )
        assert decision.deactivation_required is True
    expired = evaluate_shadow_activation_health(
        ctx["snapshot"],
        ctx["monitoring_plan"],
        activation_window_end=NOW - timedelta(seconds=1),
        maximum_runs=ctx["request"].maximum_runs,
        now=NOW,
    )
    assert "activation_window_expired" in expired.trigger_codes
    exhausted = evaluate_shadow_activation_health(
        ShadowActivationHealthSnapshot(
            activation_candidate_id=ctx["candidate"].activation_candidate_id,
            run_count=ctx["request"].maximum_runs,
            observed_at=NOW,
        ),
        ctx["monitoring_plan"],
        activation_window_end=ctx["request"].activation_window_end,
        maximum_runs=ctx["request"].maximum_runs,
        now=NOW,
    )
    assert "run_count_exhausted" in exhausted.trigger_codes
