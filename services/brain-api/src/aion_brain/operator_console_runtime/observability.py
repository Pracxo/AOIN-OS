"""Bounded observability counters for the AION-237 local bridge."""

from __future__ import annotations

from collections import Counter

from aion_brain.contracts.operator_console_integration import (
    PROHIBITED_COUNTER_NAMES,
    OperatorConsoleObservabilitySnapshot,
)


class OperatorConsoleObservabilityRecorder:
    """Accumulate safe counters without retaining request or response payloads."""

    def __init__(self) -> None:
        self._request_counts_by_route: Counter[str] = Counter()
        self._status_code_counts: Counter[str] = Counter()
        self._counters: Counter[str] = Counter()
        self._prohibited_counters: dict[str, int] = {
            name: 0 for name in PROHIBITED_COUNTER_NAMES
        }

    def record_route(self, route_path: str) -> None:
        self._request_counts_by_route[route_path] += 1

    def record_status(self, status_code: int) -> None:
        self._status_code_counts[str(status_code)] += 1

    def increment(self, name: str, amount: int = 1) -> None:
        self._counters[name] += amount

    def set_counter(self, name: str, value: int) -> None:
        self._counters[name] = value

    def counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def request_counts_by_route(self) -> dict[str, int]:
        return dict(sorted(self._request_counts_by_route.items()))

    def status_code_counts(self) -> dict[str, int]:
        return dict(sorted(self._status_code_counts.items()))

    def counters(self) -> dict[str, int]:
        return dict(sorted(self._counters.items()))

    def prohibited_counters(self) -> dict[str, int]:
        return dict(sorted(self._prohibited_counters.items()))

    def snapshot(self) -> OperatorConsoleObservabilitySnapshot:
        return OperatorConsoleObservabilitySnapshot(
            request_counts_by_route=self.request_counts_by_route(),
            status_code_counts=self.status_code_counts(),
            counters=self.counters(),
        )
