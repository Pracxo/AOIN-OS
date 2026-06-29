from __future__ import annotations

from aion_brain.connector_simulator import (
    ConnectorDryRunSimulator,
    ConnectorPolicyReadinessService,
    ConnectorResponseShapeValidator,
    ConnectorShapeValidator,
)
from aion_brain.contracts.connector_simulator import (
    ConnectorPolicyReadinessRequest,
    ConnectorSimulationRequest,
)
from tests.operator_action_fakes import FakeTelemetry


def test_visual_telemetry_emits_connector_simulator_events() -> None:
    telemetry = FakeTelemetry()
    ConnectorDryRunSimulator(
        request_validator=ConnectorShapeValidator(),
        response_validator=ConnectorResponseShapeValidator(),
        telemetry_service=telemetry,
    ).simulate(
        ConnectorSimulationRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
        )
    )
    ConnectorPolicyReadinessService(telemetry_service=telemetry).check(
        ConnectorPolicyReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            declared_policy_actions=[
                "connector_simulator.simulate",
                "connector_simulator.replay",
                "connector_simulator.policy_readiness",
            ],
        )
    )

    event_types = {getattr(event, "event_type", None) for event in telemetry.events}
    node_types = {getattr(event, "node_type", None) for event in telemetry.events}
    assert "connector_simulation_completed" in event_types
    assert "connector_policy_readiness_checked" in event_types
    assert "connector_simulation" in node_types
    assert "connector_policy_readiness" in node_types
