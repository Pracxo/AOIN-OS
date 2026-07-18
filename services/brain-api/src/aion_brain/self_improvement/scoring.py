"""Deterministic benchmark scoring for self-improvement evaluation."""

from __future__ import annotations

import math
from collections.abc import Iterable

from aion_brain.self_improvement.benchmark_contracts import (
    REQUIRED_BENCHMARK_METRICS,
    BenchmarkMetric,
    BenchmarkMetricName,
    BenchmarkSafetyGate,
)


def metric_map(metrics: Iterable[BenchmarkMetric]) -> dict[BenchmarkMetricName, BenchmarkMetric]:
    """Return metrics keyed by name, rejecting duplicate metric names."""

    mapped: dict[BenchmarkMetricName, BenchmarkMetric] = {}
    for metric in metrics:
        if metric.metric_name in mapped:
            raise ValueError(f"duplicate benchmark metric: {metric.metric_name}")
        mapped[metric.metric_name] = metric
    return mapped


def require_required_metric_set(
    metrics: Iterable[BenchmarkMetric],
) -> dict[BenchmarkMetricName, BenchmarkMetric]:
    """Validate that all AION-168 required metrics are present exactly once."""

    mapped = metric_map(metrics)
    missing = set(REQUIRED_BENCHMARK_METRICS) - set(mapped)
    extra = set(mapped) - set(REQUIRED_BENCHMARK_METRICS)
    if missing or extra:
        raise ValueError(
            "benchmark metrics must match required set; "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )
    return mapped


def metric_meets_threshold(metric: BenchmarkMetric) -> bool:
    """Return whether one metric meets its threshold."""

    if metric.higher_is_better:
        return metric.value >= metric.threshold
    return metric.value <= metric.threshold


def metrics_meet_thresholds(metrics: Iterable[BenchmarkMetric]) -> bool:
    """Return whether all required metrics meet their thresholds."""

    mapped = require_required_metric_set(metrics)
    return all(metric_meets_threshold(mapped[name]) for name in REQUIRED_BENCHMARK_METRICS)


def normalized_metric_score(metric: BenchmarkMetric) -> float:
    """Normalize a metric against its threshold using deterministic arithmetic."""

    if metric.higher_is_better:
        if metric.threshold == 0.0:
            return 1.0
        return min(1.0, metric.value / metric.threshold)
    if metric.threshold == 0.0:
        return 1.0 if metric.value == 0.0 else 0.0
    if metric.value <= metric.threshold:
        return 1.0
    return max(0.0, metric.threshold / metric.value)


def score_metric_set(metrics: Iterable[BenchmarkMetric]) -> float:
    """Compute a weighted deterministic quality score for the required metric set."""

    mapped = require_required_metric_set(metrics)
    weighted_scores = []
    weights = []
    for name in REQUIRED_BENCHMARK_METRICS:
        metric = mapped[name]
        weighted_scores.append(normalized_metric_score(metric) * metric.weight)
        weights.append(metric.weight)
    total_weight = math.fsum(weights)
    if total_weight == 0.0:
        raise ValueError("at least one benchmark metric must have positive weight")
    return math.fsum(weighted_scores) / total_weight


def change_is_eligible(
    metrics: Iterable[BenchmarkMetric],
    safety_gate: BenchmarkSafetyGate,
) -> bool:
    """Return fail-closed change eligibility for metrics plus hard safety gates."""

    return safety_gate.change_eligible and metrics_meet_thresholds(metrics)


__all__ = [
    "change_is_eligible",
    "metric_map",
    "metric_meets_threshold",
    "metrics_meet_thresholds",
    "normalized_metric_score",
    "require_required_metric_set",
    "score_metric_set",
]
