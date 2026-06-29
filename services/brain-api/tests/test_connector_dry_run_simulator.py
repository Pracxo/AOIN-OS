from __future__ import annotations

from aion_brain.connector_simulator import (
    ConnectorDryRunSimulator,
    ConnectorResponseShapeValidator,
    ConnectorShapeValidator,
)
from aion_brain.contracts.connector_simulator import ConnectorSimulationRequest


def test_connector_dry_run_simulator_returns_synthetic_untrusted_result() -> None:
    result = ConnectorDryRunSimulator(
        request_validator=ConnectorShapeValidator(),
        response_validator=ConnectorResponseShapeValidator(),
    ).simulate(
        ConnectorSimulationRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            request_shape={"object": "synthetic_request"},
            expected_response_shape={"object": "synthetic_response"},
        )
    )

    assert result.status == "warning"
    assert result.synthetic is True
    assert result.trusted is False
    assert result.external_calls_made is False
    assert result.credentials_used is False
    assert result.tokens_used is False
    assert result.connector_runtime_enabled is False
    assert result.findings[0]["finding_type"] == "untrusted_ingress"
