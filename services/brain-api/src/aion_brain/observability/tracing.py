"""Observability placeholder."""


class ObservabilityTracer:
    """Adapter boundary for future tracing systems such as Langfuse."""

    def start_trace(self, trace_id: str) -> None:
        """Start a future observability trace."""
        raise NotImplementedError("Observability integration is not implemented in v0.1.")
