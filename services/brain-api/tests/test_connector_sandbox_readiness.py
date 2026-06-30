from __future__ import annotations

from aion_brain.connector_sandbox import (
    ConnectorIsolationBoundaryService,
    ConnectorSandboxCapabilityRuleService,
    ConnectorSandboxDenialService,
    ConnectorSandboxDesignService,
    ConnectorSandboxReadinessService,
)
from aion_brain.contracts.connector_sandbox import ConnectorSandboxReadinessRequest


def _service() -> ConnectorSandboxReadinessService:
    design = ConnectorSandboxDesignService()
    boundary = ConnectorIsolationBoundaryService(design)
    capabilities = ConnectorSandboxCapabilityRuleService()
    denials = ConnectorSandboxDenialService()
    return ConnectorSandboxReadinessService(
        boundary_service=boundary,
        capability_service=capabilities,
        denial_service=denials,
    )


def test_connector_sandbox_readiness_allows_preview_only() -> None:
    result = _service().evaluate(
        ConnectorSandboxReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            requested_capabilities=["connector.sandbox.readiness.preview"],
        )
    )

    assert result.status == "ready"
    assert result.sandbox_ready is True
    assert result.runtime_execution_allowed is False
    assert result.filesystem_access_allowed is False
    assert result.network_access_allowed is False
    assert result.credential_access_allowed is False
    assert result.token_access_allowed is False


def test_connector_sandbox_readiness_blocks_runtime_capability() -> None:
    result = _service().evaluate(
        ConnectorSandboxReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            requested_capabilities=["connector.sandbox.runtime.execute"],
        )
    )

    assert result.status == "blocked"
    assert result.sandbox_ready is False
    assert result.runtime_execution_allowed is False
    assert any(item["blocker_key"] == "explicit_sandbox_denial_rule" for item in result.blockers)
