"""Status query helpers for disabled connector runtime."""

from __future__ import annotations

from aion_brain.connector_runtime.gate import ConnectorRuntimeGateService
from aion_brain.contracts.connector_runtime import ConnectorRuntimeStatus


class ConnectorRuntimeQueryService:
    """Expose disabled connector-runtime status without mutating state."""

    def __init__(self, gate_service: ConnectorRuntimeGateService) -> None:
        self._gate_service = gate_service

    def status(self, scope: list[str]) -> ConnectorRuntimeStatus:
        """Return current disabled connector-runtime status."""

        return self._gate_service.status(scope)


__all__ = ["ConnectorRuntimeQueryService"]
