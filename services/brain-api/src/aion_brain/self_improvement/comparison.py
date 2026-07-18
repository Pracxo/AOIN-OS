"""Deterministic benchmark comparison methods."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence

from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.benchmark_contracts import (
    LOWER_IS_BETTER_METRICS,
    REQUIRED_BENCHMARK_METRICS,
    BenchmarkBaseline,
    BenchmarkCandidateResult,
    BenchmarkComparison,
    BenchmarkMetricDelta,
)
from aion_brain.self_improvement.scoring import metric_map, score_metric_set

DETERMINISTIC_COMPARISON_METHOD = "deterministic_paired_delta_interval"


def deterministic_paired_delta_interval(
    baseline_values: Sequence[float],
    candidate_values: Sequence[float],
    *,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Return mean delta and a deterministic percentile interval over paired deltas.

    The method is intentionally non-random: it computes paired deltas, sorts them,
    and returns nearest-rank interval bounds. It documents uncertainty without
    introducing random bootstrap variance into CI.
    """

    if len(baseline_values) != len(candidate_values):
        raise ValueError("baseline and candidate values must have equal length")
    if not baseline_values:
        raise ValueError("at least one paired value is required")
    if confidence <= 0.0 or confidence >= 1.0:
        raise ValueError("confidence must be between 0 and 1")

    deltas = sorted(
        candidate - baseline
        for baseline, candidate in zip(baseline_values, candidate_values, strict=True)
    )
    alpha = 1.0 - confidence
    low_index = max(0, math.floor((alpha / 2.0) * (len(deltas) - 1)))
    high_index = min(len(deltas) - 1, math.ceil((1.0 - alpha / 2.0) * (len(deltas) - 1)))
    return statistics.fmean(deltas), deltas[low_index], deltas[high_index]


def compare_baseline_to_candidate(
    *,
    comparison_id: str,
    baseline: BenchmarkBaseline,
    candidate_result: BenchmarkCandidateResult,
) -> BenchmarkComparison:
    """Compare baseline and candidate metrics without allowing safety offsets."""

    if baseline.baseline_id != candidate_result.baseline_id:
        raise ValueError("candidate result must reference the compared baseline")
    if baseline.manifest_id != candidate_result.manifest_id:
        raise ValueError("candidate result must reference the compared manifest")
    if baseline.manifest_fingerprint != candidate_result.manifest_fingerprint:
        raise ValueError("candidate result must use the baseline manifest fingerprint")

    baseline_metrics = metric_map(baseline.metrics)
    candidate_metrics = metric_map(candidate_result.metrics)
    metric_deltas = []
    baseline_values = []
    candidate_values = []
    for metric_name in REQUIRED_BENCHMARK_METRICS:
        baseline_metric = baseline_metrics[metric_name]
        candidate_metric = candidate_metrics[metric_name]
        delta = candidate_metric.value - baseline_metric.value
        improved = delta < 0.0 if metric_name in LOWER_IS_BETTER_METRICS else delta > 0.0
        metric_deltas.append(
            BenchmarkMetricDelta(
                metric_name=metric_name,
                baseline_value=baseline_metric.value,
                candidate_value=candidate_metric.value,
                delta=delta,
                improved=improved,
            )
        )
        baseline_values.append(baseline_metric.value)
        candidate_values.append(candidate_metric.value)

    _, interval_low, interval_high = deterministic_paired_delta_interval(
        baseline_values,
        candidate_values,
    )
    baseline_score = score_metric_set(baseline.metrics)
    candidate_score = score_metric_set(candidate_result.metrics)
    safety_passed = candidate_result.safety_gate.change_eligible

    return BenchmarkComparison(
        comparison_id=comparison_id,
        baseline_id=baseline.baseline_id,
        candidate_result_id=candidate_result.candidate_result_id,
        method=DETERMINISTIC_COMPARISON_METHOD,
        metric_deltas=tuple(metric_deltas),
        baseline_quality_score=baseline_score,
        candidate_quality_score=candidate_score,
        quality_score_delta=candidate_score - baseline_score,
        confidence_interval_low=interval_low,
        confidence_interval_high=interval_high,
        safety_passed=safety_passed,
        change_eligible=safety_passed and candidate_score >= baseline_score,
        reason_codes=() if safety_passed else ("hard_safety_gate_failed",),
        created_at=utc_now(),
    )


__all__ = [
    "DETERMINISTIC_COMPARISON_METHOD",
    "compare_baseline_to_candidate",
    "deterministic_paired_delta_interval",
]
