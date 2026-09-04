"""Observability snapshots for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import LiveProviderObservabilitySnapshot


def create_observability_snapshot(
    *,
    snapshot_id: str,
    counters: dict[str, int],
    latencies_ms: tuple[int, ...],
    created_at: datetime,
) -> LiveProviderObservabilitySnapshot:
    """Create deterministic latency and counter evidence."""

    summary = _latency_summary(latencies_ms)
    return LiveProviderObservabilitySnapshot(
        snapshot_id=snapshot_id,
        counters=counters,
        latency_summary=summary,
        created_at=created_at,
    )


def _latency_summary(values: tuple[int, ...]) -> dict[str, int]:
    if not values:
        return {"mean": 0, "p50": 0, "p95": 0, "maximum": 0}
    ordered = tuple(sorted(values))
    total = sum(ordered)
    index_50 = min(len(ordered) - 1, len(ordered) // 2)
    index_95 = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
    return {
        "mean": int(round(total / len(ordered))),
        "p50": ordered[index_50],
        "p95": ordered[index_95],
        "maximum": ordered[-1],
    }
