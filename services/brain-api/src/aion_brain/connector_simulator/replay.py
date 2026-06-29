"""Synthetic connector replay service."""

from __future__ import annotations

from typing import Protocol

from aion_brain.contracts.connector_simulator import (
    ConnectorReplayFixture,
    ConnectorSimulationRequest,
    ConnectorSimulationResult,
)


class _ConnectorSimulator(Protocol):
    def simulate(self, request: ConnectorSimulationRequest) -> ConnectorSimulationResult:
        """Run one synthetic connector simulation."""
        ...


class ConnectorReplayService:
    """Replay local fixture shapes through the dry-run simulator."""

    def __init__(self, simulator: _ConnectorSimulator) -> None:
        self._simulator = simulator

    def replay(self, fixture: ConnectorReplayFixture) -> ConnectorSimulationResult:
        """Replay one synthetic fixture without external calls."""

        request = ConnectorSimulationRequest(
            connector_simulation_request_id=f"replay-{fixture.replay_fixture_id}",
            connector_key=fixture.connector_key,
            owner_scope=fixture.owner_scope,
            simulation_type="dry_run",
            request_shape=fixture.request_shape,
            expected_response_shape=fixture.response_shape,
            evidence_refs=["docs/connectors/synthetic-connector-replay.md"],
            metadata={
                "fixture_type": fixture.fixture_type,
                "expected_findings": fixture.expected_findings,
            },
        )
        result = self._simulator.simulate(request)
        return result.model_copy(
            update={
                "metadata": {
                    **result.metadata,
                    "replay_fixture_id": fixture.replay_fixture_id,
                    "replay_name": fixture.name,
                }
            }
        )


__all__ = ["ConnectorReplayService"]
