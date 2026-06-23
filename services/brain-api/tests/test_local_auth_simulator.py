from __future__ import annotations

from aion_brain.contracts.local_auth import DevIdentitySimulationRequest
from aion_brain.local_auth.simulator import DevIdentitySimulator
from tests.kernel_fakes import FakeTelemetry


def test_dev_identity_simulator_returns_context_and_visual_telemetry() -> None:
    telemetry = FakeTelemetry()
    context = DevIdentitySimulator(telemetry_service=telemetry).simulate(
        DevIdentitySimulationRequest(
            trace_id="trace-local-auth-1",
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
        )
    )

    assert context.actor_id == "local.operator"
    assert context.production_auth is False
    assert telemetry.events
    assert telemetry.events[0].event_type == "local_auth_context_simulated"
    assert telemetry.events[0].node_type == "local_auth_context"
