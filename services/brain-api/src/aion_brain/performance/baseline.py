"""Capacity baseline service."""

from __future__ import annotations

import platform
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.performance import BenchmarkRun, CapacityBaseline
from aion_brain.performance.repository import PerformanceRepository
from aion_brain.performance.timing import percentile


class CapacityBaselineService:
    """Create deterministic local capacity baselines from benchmark runs."""

    def __init__(
        self,
        repository: PerformanceRepository,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_from_run(
        self,
        version: str,
        baseline_name: str,
        benchmark_run_ids: list[str],
        created_by: str | None,
    ) -> CapacityBaseline:
        """Create a capacity baseline from stored benchmark run ids."""
        runs = [
            run
            for run_id in benchmark_run_ids
            if (run := self._repository.get_run(run_id)) is not None
        ]
        metrics = compute_run_metrics(runs)
        baseline = CapacityBaseline(
            capacity_baseline_id=f"capacity-baseline-{uuid4().hex}",
            version=version,
            baseline_name=baseline_name,
            status="active" if runs else "failed",
            environment={
                "python_version": platform.python_version(),
                "aion_version": self._settings.version,
                "api_version": self._settings.api_version,
                "optional_adapters_required": False,
            },
            metrics=metrics,
            thresholds={"regression_warning_percent": 10, "regression_failure_percent": 25},
            benchmark_run_ids=[run.benchmark_run_id for run in runs],
            report={
                "run_count": len(runs),
                "sample_count": sum(run.sample_count for run in runs),
                "external_calls": False,
            },
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_baseline(baseline)
        _emit(
            self._telemetry_service,
            "capacity_baseline_created",
            saved.capacity_baseline_id,
            saved.report,
            0.6,
        )
        return saved

    def get(self, capacity_baseline_id: str) -> CapacityBaseline | None:
        """Return one baseline."""
        return self._repository.get_baseline(capacity_baseline_id)

    def list(
        self,
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> list[CapacityBaseline]:
        """List baselines."""
        return self._repository.list_baselines(version=version, status=status)


def compute_run_metrics(runs: list[BenchmarkRun]) -> dict[str, Any]:
    """Compute per-operation latency metrics for benchmark runs."""
    by_operation: dict[str, list[int]] = defaultdict(list)
    error_count = 0
    warning_count = 0
    for run in runs:
        for sample in run.samples:
            by_operation[sample.operation_type].append(sample.duration_ms)
            if sample.status == "failed":
                error_count += 1
            if sample.status == "warning":
                warning_count += 1
    operations: dict[str, dict[str, float | int]] = {}
    for operation, durations in sorted(by_operation.items()):
        operations[operation] = {
            "sample_count": len(durations),
            "p50_ms": percentile(durations, 50),
            "p95_ms": percentile(durations, 95),
            "p99_ms": percentile(durations, 99),
            "max_ms": float(max(durations)) if durations else 0.0,
        }
    return {
        "operations": operations,
        "sample_count": sum(len(values) for values in by_operation.values()),
        "error_count": error_count,
        "warning_count": warning_count,
        "total_duration_ms": sum(sum(values) for values in by_operation.values()),
    }


def _emit(
    telemetry: object | None,
    event_type: str,
    node_id: str,
    payload: dict[str, Any],
    intensity: float,
) -> None:
    emit = getattr(telemetry, "emit", None)
    if not callable(emit):
        return
    from aion_brain.contracts.telemetry import VisualTelemetryEvent

    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                trace_id=node_id,
                event_type=event_type,  # type: ignore[arg-type]
                node_type="baseline",
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=intensity,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
