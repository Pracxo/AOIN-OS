"""Connector sandbox isolation boundary model."""

from __future__ import annotations

from aion_brain.connector_sandbox.design import ConnectorSandboxDesignService
from aion_brain.contracts.connector_sandbox import ConnectorSandboxBoundary
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorIsolationBoundaryService:
    """Expose connector sandbox isolation boundaries as read-only evidence."""

    def __init__(
        self,
        design_service: ConnectorSandboxDesignService,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._design_service = design_service
        self._telemetry_service = telemetry_service

    def boundary(self) -> ConnectorSandboxBoundary:
        """Return isolation boundary evidence without enabling sandbox access."""

        boundary = self._design_service.boundary()
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_sandbox_boundary_read",
            node_type="connector_sandbox_boundary",
            node_id=boundary.sandbox_boundary_id,
            intensity=0.45,
            trace_id="connector-sandbox-boundary-local",
            payload={
                "runtime_execution_allowed": False,
                "filesystem_access_allowed": False,
                "network_access_allowed": False,
            },
        )
        return boundary


__all__ = ["ConnectorIsolationBoundaryService"]
