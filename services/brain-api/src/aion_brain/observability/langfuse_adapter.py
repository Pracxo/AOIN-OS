"""Future Langfuse observability adapter placeholder."""

from aion_brain.contracts.observability import ObservabilityEvent, ObservabilitySummary


class LangfuseAdapter:
    """Langfuse is planned as AION's optional observability adapter.

    AION contracts must remain independent of Langfuse internals.
    """

    def record_event(self, event: ObservabilityEvent) -> ObservabilityEvent:
        """Reserve event recording for a future adapter."""
        raise NotImplementedError("Langfuse adapter is reserved for a later AION task.")

    def summarize(self, scope: list[str]) -> ObservabilitySummary:
        """Reserve summary reads for a future adapter."""
        raise NotImplementedError("Langfuse adapter is reserved for a later AION task.")
