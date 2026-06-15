"""Local stub runtime for non-executing module tests and placeholders."""

from datetime import UTC, datetime

from aion_brain.contracts.modules import (
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    ModuleHealthCheck,
    ModuleRuntime,
)


class LocalStubRuntimeAdapter:
    """Healthy runtime that intentionally never executes capabilities."""

    def health_check(self, runtime: ModuleRuntime) -> ModuleHealthCheck:
        """Return healthy for the local stub boundary."""
        return ModuleHealthCheck(
            health_check_id=f"health-{runtime.runtime_id}-{datetime.now(UTC).timestamp()}",
            runtime_id=runtime.runtime_id,
            module_id=runtime.module_id,
            status="healthy",
            latency_ms=0,
            details={"runtime_type": runtime.runtime_type, "executes": False},
            created_at=datetime.now(UTC),
        )

    def invoke(
        self,
        request: CapabilityInvocationRequest,
        runtime: ModuleRuntime,
    ) -> CapabilityInvocationResult:
        """Return a structured not-implemented result."""
        return CapabilityInvocationResult(
            invocation_id=request.invocation_id,
            capability_id=request.capability_id,
            runtime_id=runtime.runtime_id,
            status="not_implemented",
            output={"reason": "Local stub runtime does not execute capabilities."},
            error={},
            policy_decision_id=None,
            latency_ms=0,
            created_at=datetime.now(UTC),
        )
