from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.connector_simulator import (
    ConnectorPolicyReadinessRequest,
    ConnectorPolicyReadinessResult,
    ConnectorReplayFixture,
    ConnectorSimulationRequest,
    ConnectorSimulationResult,
    utc_now,
)


def test_connector_simulation_request_rejects_runtime_material() -> None:
    request = ConnectorSimulationRequest(
        connector_key="mock.local.preview",
        owner_scope=["workspace:main"],
        request_shape={"object": "synthetic_request"},
        expected_response_shape={"object": "synthetic_response"},
    )

    assert request.simulation_type == "dry_run"

    with pytest.raises(ValidationError):
        ConnectorSimulationRequest(
            connector_key="Mock.Local",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        ConnectorSimulationRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            simulation_type="live",
        )
    with pytest.raises(ValidationError):
        ConnectorSimulationRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            request_shape={"endpoint": "external"},
        )


def test_connector_simulation_result_requires_synthetic_disabled_state() -> None:
    result = ConnectorSimulationResult(
        connector_simulation_result_id="connector-simulation-test",
        connector_key="mock.local.preview",
        status="warning",
        simulation_type="dry_run",
        synthetic=True,
        trusted=False,
        external_calls_made=False,
        credentials_used=False,
        tokens_used=False,
        connector_runtime_enabled=False,
        request_hash="request-hash",
        response_hash="response-hash",
        score=0.75,
        created_at=utc_now(),
    )

    assert result.synthetic is True
    assert result.trusted is False

    with pytest.raises(ValidationError):
        ConnectorSimulationResult(
            **result.model_copy(update={"external_calls_made": True}).model_dump()
        )


def test_replay_and_policy_readiness_contracts_keep_runtime_blocked() -> None:
    fixture = ConnectorReplayFixture(
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
    request = ConnectorPolicyReadinessRequest(
        connector_key="mock.local.preview",
        owner_scope=["workspace:main"],
    )
    result = ConnectorPolicyReadinessResult(
        connector_policy_readiness_id="readiness-1",
        connector_key=request.connector_key,
        status="blocked",
        policy_ready=False,
        sandbox_ready=True,
        audit_ready=True,
        provenance_ready=True,
        external_calls_allowed=False,
        credentials_allowed=False,
        activation_allowed=False,
        created_at=utc_now(),
    )

    assert fixture.synthetic is True
    assert fixture.trusted is False
    assert result.external_calls_allowed is False

    with pytest.raises(ValidationError):
        ConnectorPolicyReadinessResult(
            **result.model_copy(update={"activation_allowed": True}).model_dump()
        )
