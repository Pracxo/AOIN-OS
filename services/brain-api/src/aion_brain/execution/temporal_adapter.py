"""Temporal execution adapter placeholder."""

from aion_brain.contracts.execution import ExecutionRequest, ExecutionRun


class TemporalAdapter:
    """Temporal is planned as AION's durable workflow adapter. AION contracts must remain independent of Temporal internals."""  # noqa: E501

    def execute(self, request: ExecutionRequest) -> ExecutionRun:
        """Execute through a future Temporal adapter."""
        raise NotImplementedError("Temporal workflow integration is not implemented in v0.1.")
