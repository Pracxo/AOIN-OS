from __future__ import annotations

from aion_brain.connector_simulator import ConnectorPolicyReadinessService
from aion_brain.contracts.connector_simulator import ConnectorPolicyReadinessRequest


def test_connector_policy_readiness_requires_simulator_actions() -> None:
    result = ConnectorPolicyReadinessService().check(
        ConnectorPolicyReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            declared_policy_actions=["connector_simulator.simulate"],
        )
    )

    assert result.status == "blocked"
    assert result.policy_ready is False
    assert "connector_simulator.replay" in result.missing_policy_actions
    assert result.external_calls_allowed is False
    assert result.credentials_allowed is False
    assert result.activation_allowed is False


def test_connector_policy_readiness_passes_without_runtime_approval() -> None:
    result = ConnectorPolicyReadinessService().check(
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

    assert result.status == "passed"
    assert result.policy_ready is True
    assert result.external_calls_allowed is False
