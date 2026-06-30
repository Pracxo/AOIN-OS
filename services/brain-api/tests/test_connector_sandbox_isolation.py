from __future__ import annotations

from aion_brain.connector_sandbox.design import ConnectorSandboxDesignService
from aion_brain.connector_sandbox.isolation import ConnectorIsolationBoundaryService
from tests.kernel_fakes import FakeTelemetry


def test_connector_sandbox_isolation_emits_read_only_boundary() -> None:
    telemetry = FakeTelemetry()
    boundary = ConnectorIsolationBoundaryService(
        ConnectorSandboxDesignService(),
        telemetry_service=telemetry,
    ).boundary()

    assert boundary.runtime_execution_allowed is False
    assert boundary.filesystem_access_allowed is False
    assert boundary.network_access_allowed is False
    assert telemetry.events
    assert telemetry.events[-1].event_type == "connector_sandbox_boundary_read"
