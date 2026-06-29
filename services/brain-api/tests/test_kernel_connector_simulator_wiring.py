from __future__ import annotations

from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_kernel_wires_connector_simulator_services() -> None:
    container = kernel_container()

    assert container.connector_dry_run_simulator is not None
    assert container.connector_replay_service is not None
    assert container.connector_policy_readiness_service is not None
    assert container.connector_simulator_query_service is not None

    names = {check.name for check in KernelDiagnostics(container).run()}
    assert "connector_simulator_services_present" in names
    assert "connector_simulator_external_calls_enabled" in names
    assert "connector_simulator_runtime_activation_enabled" in names
