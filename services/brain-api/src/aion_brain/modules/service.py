"""Module bus service facade."""

from aion_brain.contracts.modules import (
    CapabilityBindingRequest,
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    CapabilityRuntimeBinding,
    ModuleHealthCheck,
    ModuleRuntime,
    ModuleRuntimeRegistrationRequest,
    ModuleRuntimeRegistrationResponse,
)
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway


class ModuleRuntimeService:
    """Thin service wrapper around the capability runtime gateway."""

    def __init__(self, gateway: CapabilityRuntimeGateway) -> None:
        self._gateway = gateway

    def register_runtime(
        self,
        request: ModuleRuntimeRegistrationRequest,
    ) -> ModuleRuntimeRegistrationResponse:
        """Register a runtime through the gateway."""
        return self._gateway.register_runtime(request)

    def bind_capability(self, request: CapabilityBindingRequest) -> CapabilityRuntimeBinding:
        """Bind a capability through the gateway."""
        return self._gateway.bind_capability(request)

    def list_runtimes(self) -> list[ModuleRuntime]:
        """List registered runtimes."""
        return self._gateway.list_runtimes()

    def get_runtime(self, runtime_id: str) -> ModuleRuntime | None:
        """Return a registered runtime."""
        return self._gateway.get_runtime(runtime_id)

    def health_check(self, runtime_id: str) -> ModuleHealthCheck:
        """Check runtime health."""
        return self._gateway.health_check(runtime_id)

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityInvocationResult:
        """Invoke a capability through the runtime gateway."""
        return self._gateway.invoke(request)
