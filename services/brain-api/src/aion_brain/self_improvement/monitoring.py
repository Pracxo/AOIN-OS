"""Canary metric monitoring for AION-174 self-improvement."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from aion_brain.self_improvement.benchmark_contracts import (
    HIGHER_IS_BETTER_METRICS,
    LOWER_IS_BETTER_METRICS,
    BenchmarkMetricName,
)
from aion_brain.self_improvement.canary_contracts import (
    ROLLBACK_TRIGGERS,
    CanaryObservation,
    CanaryPlan,
    RollbackTrigger,
)
from aion_brain.self_improvement.scoring import metric_map


class CanaryMonitoringSummary(BaseModel):
    """Aggregated health summary for a canary monitoring window."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_id: str
    observations_evaluated: int = Field(ge=0)
    healthy: bool
    rollback_triggers: tuple[RollbackTrigger, ...] = Field(default_factory=tuple)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)


class CanaryMonitor:
    """Evaluate canary observations against approved metric thresholds."""

    def summarize(
        self,
        plan: CanaryPlan,
        observations: tuple[CanaryObservation, ...],
    ) -> CanaryMonitoringSummary:
        """Return a fail-closed summary for the supplied canary observations."""

        if not observations:
            return CanaryMonitoringSummary(
                plan_id=plan.plan_id,
                observations_evaluated=0,
                healthy=False,
                rollback_triggers=("unexpected_runtime_effect",),
                reason_codes=("no_canary_observations",),
            )

        triggers: list[RollbackTrigger] = []
        reasons: list[str] = []
        threshold_by_name = {
            threshold.metric_name: threshold for threshold in plan.metric_thresholds
        }
        required = {threshold.metric_name for threshold in plan.metric_thresholds}

        for observation in observations:
            if observation.plan_id != plan.plan_id:
                triggers.append("unexpected_runtime_effect")
                reasons.append("observation_plan_mismatch")
                continue
            if observation.unexpected_runtime_effect:
                triggers.append("unexpected_runtime_effect")
                reasons.append("unexpected_runtime_effect")
            if observation.policy_violation_count > 0:
                triggers.append("policy_violation")
                reasons.append("policy_violation")
            if observation.security_regression_count > 0:
                triggers.append("security_regression")
                reasons.append("security_regression")

            metric_by_name = metric_map(observation.metrics)
            missing = required - set(metric_by_name)
            if missing:
                triggers.append("benchmark_drift")
                reasons.append("missing_canary_metric")
            for metric_name in required & set(metric_by_name):
                metric = metric_by_name[metric_name]
                threshold = threshold_by_name[metric_name]
                if _metric_violates_threshold(metric_name, metric.value, threshold.threshold):
                    triggers.append(threshold.rollback_trigger)
                    reasons.append(f"{metric_name}_threshold_violated")

        unique_triggers = _unique_ordered(tuple(triggers))
        if not unique_triggers:
            reasons.append("canary_metrics_healthy")
        return CanaryMonitoringSummary(
            plan_id=plan.plan_id,
            observations_evaluated=len(observations),
            healthy=not unique_triggers,
            rollback_triggers=unique_triggers,
            reason_codes=_unique_ordered(tuple(reasons)),
        )


def _metric_violates_threshold(
    metric_name: BenchmarkMetricName,
    value: float,
    threshold: float,
) -> bool:
    if metric_name in HIGHER_IS_BETTER_METRICS:
        return value < threshold
    if metric_name in LOWER_IS_BETTER_METRICS:
        return value > threshold
    return True


def _unique_ordered[TextT: str](values: tuple[TextT, ...]) -> tuple[TextT, ...]:
    seen: set[TextT] = set()
    result: list[TextT] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def required_rollback_triggers() -> tuple[RollbackTrigger, ...]:
    """Return every required rollback trigger for safety checks."""

    return ROLLBACK_TRIGGERS


__all__ = [
    "CanaryMonitor",
    "CanaryMonitoringSummary",
    "required_rollback_triggers",
]
