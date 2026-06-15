"""Performance regression comparison."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.performance import (
    BenchmarkRun,
    CapacityBaseline,
    PerformanceRegressionReport,
)
from aion_brain.performance.baseline import compute_run_metrics
from aion_brain.performance.repository import PerformanceRepository


class PerformanceRegressionComparator:
    """Compare a benchmark run against a local capacity baseline."""

    def __init__(
        self,
        repository: PerformanceRepository,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._telemetry_service = telemetry_service

    def compare(
        self,
        run: BenchmarkRun,
        baseline: CapacityBaseline,
    ) -> PerformanceRegressionReport:
        """Compare p95 and max latency by operation."""
        current = compute_run_metrics([run]).get("operations", {})
        base = baseline.metrics.get("operations", {})
        regressions: list[dict[str, Any]] = []
        improvements: list[dict[str, Any]] = []
        for operation, metrics in current.items():
            if not isinstance(metrics, dict):
                continue
            base_metrics = base.get(operation) if isinstance(base, dict) else None
            if not isinstance(base_metrics, dict):
                continue
            current_p95 = float(metrics.get("p95_ms", 0))
            baseline_p95 = float(base_metrics.get("p95_ms", 0))
            if baseline_p95 <= 0:
                continue
            change_percent = ((current_p95 - baseline_p95) / baseline_p95) * 100
            payload = {
                "operation_type": operation,
                "baseline_p95_ms": baseline_p95,
                "current_p95_ms": current_p95,
                "change_percent": round(change_percent, 2),
                "current_max_ms": float(metrics.get("max_ms", 0)),
                "baseline_max_ms": float(base_metrics.get("max_ms", 0)),
            }
            if change_percent > 25:
                regressions.append({**payload, "severity": "failed"})
            elif change_percent >= 10:
                regressions.append({**payload, "severity": "warning"})
            elif change_percent < -10:
                improvements.append(payload)
        status = "failed" if any(item["severity"] == "failed" for item in regressions) else (
            "warning" if regressions else "passed"
        )
        report = PerformanceRegressionReport(
            regression_report_id=f"performance-regression-{uuid4().hex}",
            baseline_id=baseline.capacity_baseline_id,
            benchmark_run_id=run.benchmark_run_id,
            status=status,  # type: ignore[arg-type]
            regressions=regressions,
            improvements=improvements,
            report={"compared_operations": sorted(current), "external_calls": False},
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_regression_report(report)
        if saved.status != "passed":
            _emit(self._telemetry_service, saved.regression_report_id)
        return saved


def _emit(telemetry: object | None, node_id: str) -> None:
    emit = getattr(telemetry, "emit", None)
    if not callable(emit):
        return
    from aion_brain.contracts.telemetry import VisualTelemetryEvent

    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-performance-regression-{uuid4().hex}",
                trace_id=node_id,
                event_type="performance_regression_detected",
                node_type="regression",
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=1.0,
                payload={},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
