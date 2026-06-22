"""Safe local internal runtime for deterministic v0.1 capabilities."""

from datetime import UTC, datetime
from time import perf_counter
from typing import Any, cast

from aion_brain.contracts.modules import (
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    CapabilityInvocationResultStatus,
    ModuleHealthCheck,
    ModuleRuntime,
)

SAFE_LOCAL_INTERNAL_CAPABILITIES = {
    "aion.internal.noop",
    "aion.internal.echo",
    "aion.internal.validate_payload",
    "aion.internal.describe_invocation",
}


class LocalInternalRuntimeAdapter:
    """Execute only safe generic internal capabilities without external side effects."""

    def health_check(self, runtime: ModuleRuntime) -> ModuleHealthCheck:
        """Return healthy for the in-process deterministic runtime."""
        return ModuleHealthCheck(
            health_check_id=f"health-{runtime.runtime_id}-{_stamp()}",
            runtime_id=runtime.runtime_id,
            module_id=runtime.module_id,
            status="healthy",
            latency_ms=0,
            details={"runtime_type": runtime.runtime_type, "safe_capabilities": True},
            created_at=datetime.now(UTC),
        )

    def invoke(
        self,
        request: CapabilityInvocationRequest,
        runtime: ModuleRuntime,
    ) -> CapabilityInvocationResult:
        """Invoke one of the v0.1 safe internal capabilities."""
        started = perf_counter()
        if request.capability_id not in SAFE_LOCAL_INTERNAL_CAPABILITIES:
            return _result(
                request,
                runtime,
                "not_implemented",
                {},
                {"reason": "capability_not_supported_by_local_internal_runtime"},
                started,
            )

        output = _execute_safe_capability(request)
        return _result(request, runtime, "completed", output, {}, started)


def _execute_safe_capability(request: CapabilityInvocationRequest) -> dict[str, Any]:
    if request.capability_id == "aion.internal.noop":
        return {
            "executed": True,
            "capability": "aion.internal.noop",
            "message": "No operation performed.",
        }
    if request.capability_id == "aion.internal.echo":
        return {"executed": True, "echo": request.payload}
    if request.capability_id == "aion.internal.validate_payload":
        return {"executed": True, "valid": True, "keys": sorted(request.payload.keys())}
    return {
        "executed": True,
        "invocation_id": request.invocation_id,
        "capability_id": request.capability_id,
        "mode": request.mode,
        "execution_id": request.execution_id,
        "step_run_id": request.step_run_id,
    }


def _result(
    request: CapabilityInvocationRequest,
    runtime: ModuleRuntime,
    status: str,
    output: dict[str, Any],
    error: dict[str, Any],
    started: float,
) -> CapabilityInvocationResult:
    return CapabilityInvocationResult(
        invocation_id=request.invocation_id,
        capability_id=request.capability_id,
        runtime_id=runtime.runtime_id,
        status=cast(CapabilityInvocationResultStatus, status),
        output=output,
        error=error,
        policy_decision_id=None,
        latency_ms=max(0, int((perf_counter() - started) * 1000)),
        created_at=datetime.now(UTC),
    )


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
