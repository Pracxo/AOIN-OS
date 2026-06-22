"""Observability adapter boundary."""

from typing import Protocol

from aion_brain.contracts.observability import ObservabilityEvent, ObservabilitySummary


class ObservabilityAdapter(Protocol):
    """AION-owned interface for observability implementations."""

    def record_event(self, event: ObservabilityEvent) -> ObservabilityEvent:
        """Record an observability event."""
        ...

    def summarize(self, scope: list[str]) -> ObservabilitySummary:
        """Summarize local observability state."""
        ...
