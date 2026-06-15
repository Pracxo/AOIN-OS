"""Performance summary service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.performance import PerformanceSummary
from aion_brain.performance.repository import PerformanceRepository
from aion_brain.performance.timing import percentile


class PerformanceSummaryService:
    """Summarize local performance samples."""

    def __init__(self, repository: PerformanceRepository) -> None:
        self._repository = repository

    def summarize(
        self,
        scope: list[str],
        *,
        operation_type: str | None = None,
        window: str = "latest",
    ) -> PerformanceSummary:
        """Return local percentile summary."""
        del scope
        limit = 250 if window == "latest" else None
        samples = self._repository.list_samples(operation_type=operation_type, limit=limit)
        durations = [sample.duration_ms for sample in samples]
        return PerformanceSummary(
            window=window,
            sample_count=len(samples),
            p50_ms=percentile(durations, 50),
            p95_ms=percentile(durations, 95),
            p99_ms=percentile(durations, 99),
            max_ms=float(max(durations)) if durations else 0.0,
            error_count=sum(1 for sample in samples if sample.status == "failed"),
            generated_at=datetime.now(UTC),
        )
