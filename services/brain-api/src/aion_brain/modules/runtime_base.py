"""Runtime adapter protocol for module capability invocation."""

from typing import Protocol

from aion_brain.contracts.modules import (
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    ModuleHealthCheck,
    ModuleRuntime,
)


class CapabilityRuntimeAdapter(Protocol):
    """AION-owned adapter boundary for module runtimes."""

    def health_check(self, runtime: ModuleRuntime) -> ModuleHealthCheck:
        """Return runtime health using AION contracts only."""
        ...

    def invoke(
        self,
        request: CapabilityInvocationRequest,
        runtime: ModuleRuntime,
    ) -> CapabilityInvocationResult:
        """Invoke a capability using AION contracts only."""
        ...
