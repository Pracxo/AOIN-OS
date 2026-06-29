from __future__ import annotations

from aion_brain.connector_simulator import (
    ConnectorDryRunSimulator,
    ConnectorReplayService,
    ConnectorResponseShapeValidator,
    ConnectorShapeValidator,
)
from aion_brain.contracts.connector_simulator import ConnectorReplayFixture


def test_connector_replay_uses_synthetic_fixture_only() -> None:
    simulator = ConnectorDryRunSimulator(
        request_validator=ConnectorShapeValidator(),
        response_validator=ConnectorResponseShapeValidator(),
    )
    result = ConnectorReplayService(simulator).replay(
        ConnectorReplayFixture(
            replay_fixture_id="fixture-1",
            connector_key="mock.local.preview",
            name="Local Replay",
            description="Synthetic replay fixture.",
            owner_scope=["workspace:main"],
            fixture_type="synthetic_replay",
            request_shape={"object": "synthetic_request"},
            response_shape={"object": "synthetic_response"},
            synthetic=True,
            trusted=False,
        )
    )

    assert result.metadata["replay_fixture_id"] == "fixture-1"
    assert result.external_calls_made is False
    assert result.connector_runtime_enabled is False
