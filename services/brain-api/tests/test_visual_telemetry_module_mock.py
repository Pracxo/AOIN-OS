"""Module mock visual telemetry tests."""

from __future__ import annotations

from aion_brain.module_mock_runtime import ModuleMockSimulator
from tests.kernel_fakes import AllowPolicy
from tests.module_mock_helpers import (
    FakeTelemetry,
    bound_module,
    invocation_request,
    repository,
    settings,
)


def test_module_mock_simulator_emits_visual_telemetry_events() -> None:
    repo = repository()
    telemetry = FakeTelemetry()
    binding_services, _slot_id, binding_id = bound_module()
    simulator = ModuleMockSimulator(
        repo,
        AllowPolicy(),
        module_binding_repository=binding_services["repository"],
        telemetry_service=telemetry,
        settings=settings(),
    )

    simulator.invoke(invocation_request(binding_id))

    event_types = {getattr(event, "event_type", None) for event in telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in telemetry.events}
    assert "module_mock_invocation_started" in event_types
    assert "module_mock_invocation_completed" in event_types
    assert "module_mock_output" in event_types
    assert "module_mock_output" in node_types
