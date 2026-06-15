"""Timing helpers for local performance measurement."""

from __future__ import annotations

import json
import time
from typing import Any


def now_monotonic_ms() -> float:
    """Return a monotonic timestamp in milliseconds."""
    return time.monotonic() * 1000


def duration_ms(start_ms: float, end_ms: float) -> int:
    """Return a non-negative integer duration in milliseconds."""
    return max(0, int(round(end_ms - start_ms)))


def estimate_json_size_bytes(value: dict[str, Any]) -> int:
    """Estimate JSON payload size without logging payload content."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return len(encoded.encode())


def percentile(values: list[int], p: float) -> float:
    """Return a deterministic nearest-rank percentile."""
    if not values:
        return 0.0
    if p <= 0:
        return float(min(values))
    if p >= 100:
        return float(max(values))
    ordered = sorted(values)
    rank = (p / 100) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return float(ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction))
