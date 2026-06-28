"""Status query helpers for disabled auth runtime."""

from __future__ import annotations

from aion_brain.auth_runtime.gate import AuthRuntimeGateService
from aion_brain.contracts.auth_runtime import AuthRuntimeStatus


class AuthRuntimeQueryService:
    """Expose disabled auth-runtime status without mutating state."""

    def __init__(self, gate_service: AuthRuntimeGateService) -> None:
        self._gate_service = gate_service

    def status(self, scope: list[str]) -> AuthRuntimeStatus:
        """Return current disabled auth-runtime status."""

        return self._gate_service.status(scope)


__all__ = ["AuthRuntimeQueryService"]
