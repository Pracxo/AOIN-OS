"""HTTP module runtime placeholder."""

from aion_brain.contracts.modules import (
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    ModuleHealthCheck,
    ModuleRuntime,
)


class HttpRuntimeAdapter:
    """Placeholder for future HTTP module integration.

    HTTP module runtime is planned for future external module integration. AION
    contracts must remain independent of HTTP client internals.
    """

    def health_check(self, runtime: ModuleRuntime) -> ModuleHealthCheck:
        """HTTP health checks are intentionally unavailable in v0.1."""
        raise NotImplementedError("HTTP module runtime is a v0.1 placeholder.")

    def invoke(
        self,
        request: CapabilityInvocationRequest,
        runtime: ModuleRuntime,
    ) -> CapabilityInvocationResult:
        """HTTP invocation is intentionally unavailable in v0.1."""
        raise NotImplementedError("HTTP module runtime is a v0.1 placeholder.")
