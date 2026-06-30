from __future__ import annotations

from aion_brain.connector_policy.catalog import ConnectorPolicyCatalogService
from aion_brain.connector_policy.denials import ConnectorPolicyDenialService
from aion_brain.connector_policy.dry_run import ConnectorPolicyDryRunService
from aion_brain.connector_policy.matrix import ConnectorAuthorizationMatrixService
from aion_brain.contracts.connector_policy import ConnectorPolicyDryRunRequest


def _service() -> ConnectorPolicyDryRunService:
    return ConnectorPolicyDryRunService(
        catalog_service=ConnectorPolicyCatalogService(),
        matrix_service=ConnectorAuthorizationMatrixService(),
        denial_service=ConnectorPolicyDenialService(),
    )


def test_connector_policy_dry_run_allows_preview_only() -> None:
    result = _service().evaluate(
        ConnectorPolicyDryRunRequest(
            connector_key="mock.local.preview",
            role="operator",
            requested_action_key="connector_policy.dry_run",
            owner_scope=["workspace:main"],
        )
    )

    assert result.dry_run_allowed is True
    assert result.runtime_allowed is False
    assert result.external_call_allowed is False
    assert result.credential_access_allowed is False
    assert result.token_access_allowed is False
    assert result.activation_allowed is False


def test_connector_policy_dry_run_denies_future_runtime_action() -> None:
    result = _service().evaluate(
        ConnectorPolicyDryRunRequest(
            connector_key="mock.local.preview",
            role="admin",
            requested_action_key="connector.external.call",
            owner_scope=["workspace:main"],
        )
    )

    assert result.decision == "deny"
    assert result.dry_run_allowed is False

