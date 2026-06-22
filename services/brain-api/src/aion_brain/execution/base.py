"""Execution adapter and capability boundaries."""

from typing import Any, Protocol

from aion_brain.contracts.execution import (
    CapabilityInvocationRecord,
    ExecutionRequest,
    ExecutionRun,
)


class ExecutionAdapter(Protocol):
    """Boundary for future durable workflow engines."""

    def execute(self, request: ExecutionRequest) -> ExecutionRun:
        """Execute an AION execution request."""
        ...


class CapabilityInvocationAdapter(Protocol):
    """Boundary for future capability protocol runtimes."""

    def invoke(
        self,
        capability_id: str,
        payload: dict[str, Any],
        execution_id: str | None,
        step_run_id: str | None,
        trace_id: str | None,
    ) -> CapabilityInvocationRecord:
        """Invoke a capability through an AION-owned contract."""
        ...
