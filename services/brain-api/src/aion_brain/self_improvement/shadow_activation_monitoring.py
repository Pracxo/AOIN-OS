"""Monitoring validation for disabled shadow activation."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationHealthSnapshot,
    ShadowActivationMonitoringDecision,
    ShadowActivationMonitoringPlan,
    evaluate_shadow_activation_health,
)


def validate_monitoring_plan(
    plan: ShadowActivationMonitoringPlan,
) -> ShadowActivationMonitoringPlan:
    """Return a validated immutable monitoring plan."""

    return ShadowActivationMonitoringPlan.model_validate(plan.model_dump(mode="python"))


def evaluate_monitoring_snapshot(
    snapshot: ShadowActivationHealthSnapshot,
    plan: ShadowActivationMonitoringPlan,
    *,
    activation_window_end: datetime,
    maximum_runs: int,
    now: datetime,
) -> ShadowActivationMonitoringDecision:
    """Evaluate one monitoring snapshot without performing any action."""

    return evaluate_shadow_activation_health(
        snapshot,
        plan,
        activation_window_end=activation_window_end,
        maximum_runs=maximum_runs,
        now=now,
    )


__all__ = [
    "ShadowActivationHealthSnapshot",
    "ShadowActivationMonitoringDecision",
    "ShadowActivationMonitoringPlan",
    "evaluate_monitoring_snapshot",
    "evaluate_shadow_activation_health",
    "validate_monitoring_plan",
]
