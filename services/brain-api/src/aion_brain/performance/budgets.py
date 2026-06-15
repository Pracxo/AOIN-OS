"""Resource budget profile service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.performance import (
    BenchmarkRun,
    PerformanceSample,
    ResourceBudgetProfile,
)
from aion_brain.performance.repository import PerformanceRepository


class ResourceBudgetService:
    """Evaluate local performance records against report-only budgets."""

    def __init__(
        self,
        repository: PerformanceRepository,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._telemetry_service = telemetry_service

    def create_profile(self, profile: ResourceBudgetProfile) -> ResourceBudgetProfile:
        """Persist a budget profile."""
        saved = self._repository.save_budget_profile(profile)
        _emit(self._telemetry_service, "resource_budget_created", saved.resource_budget_profile_id)
        return saved

    def list_profiles(
        self,
        scope: list[str],
        *,
        status: str | None = None,
    ) -> list[ResourceBudgetProfile]:
        """List budget profiles visible to the caller."""
        profiles = self._repository.list_budget_profiles(status=status)
        return [profile for profile in profiles if _scope_matches(scope, profile.owner_scope)]

    def evaluate_sample(
        self,
        sample: PerformanceSample,
        profile: ResourceBudgetProfile,
    ) -> dict[str, Any]:
        """Evaluate one sample against matching duration budgets."""
        limit = _limit_for_sample(sample, profile)
        over_threshold = limit is not None and sample.duration_ms > limit
        result = {
            "status": "warning" if over_threshold else "passed",
            "operation_type": sample.operation_type,
            "duration_ms": sample.duration_ms,
            "limit_ms": limit,
            "enforcement_mode": profile.enforcement_mode,
        }
        _emit(self._telemetry_service, "resource_budget_evaluated", sample.performance_sample_id)
        return result

    def evaluate_run(self, run: BenchmarkRun, profile: ResourceBudgetProfile) -> dict[str, Any]:
        """Evaluate all samples in a run."""
        results = [self.evaluate_sample(sample, profile) for sample in run.samples]
        warnings = [result for result in results if result["status"] == "warning"]
        return {
            "status": "warning" if warnings else "passed",
            "benchmark_run_id": run.benchmark_run_id,
            "evaluated_count": len(results),
            "warning_count": len(warnings),
            "results": results,
        }


def _limit_for_sample(sample: PerformanceSample, profile: ResourceBudgetProfile) -> float | None:
    key_by_operation = {
        "api_request": "max_request_duration_ms",
        "brain_think": "max_brain_think_duration_ms",
        "retrieval_query": "max_retrieval_duration_ms",
        "memory_retrieve": "max_memory_retrieve_duration_ms",
        "visual_map": "max_visual_map_duration_ms",
    }
    key = key_by_operation.get(sample.operation_type)
    if key is None:
        return None
    value = profile.budgets.get(key)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value.isdigit():
        return float(value)
    return None


def _scope_matches(request_scope: list[str], owner_scope: list[str]) -> bool:
    return bool(set(request_scope).intersection(owner_scope))


def _emit(telemetry: object | None, event_type: str, node_id: str) -> None:
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
                node_type="budget",
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=0.5,
                payload={},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
