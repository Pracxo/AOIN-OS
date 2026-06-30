from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.connector_sandbox import (
    ConnectorSandboxBoundary,
    ConnectorSandboxCapabilityRule,
    ConnectorSandboxReadinessRequest,
    ConnectorSandboxReadinessResult,
    utc_now,
)


def test_connector_sandbox_boundary_rejects_runtime_permissions() -> None:
    boundary = ConnectorSandboxBoundary(
        sandbox_boundary_id="connector-sandbox-boundary-test",
        name="Connector Sandbox Boundary",
        description="Design-only sandbox boundary.",
        filesystem_access_allowed=False,
        network_access_allowed=False,
        credential_access_allowed=False,
        token_access_allowed=False,
        process_spawn_allowed=False,
        dynamic_import_allowed=False,
        package_install_allowed=False,
        runtime_execution_allowed=False,
        connector_activation_allowed=False,
        audit_required=True,
        provenance_required=True,
        created_at=utc_now(),
    )

    assert boundary.runtime_execution_allowed is False

    with pytest.raises(ValidationError):
        ConnectorSandboxBoundary(
            **boundary.model_copy(update={"network_access_allowed": True}).model_dump()
        )


def test_connector_sandbox_capability_rule_rejects_restricted_allow() -> None:
    preview = ConnectorSandboxCapabilityRule(
        rule_key="connector.sandbox.readiness.preview",
        title="Connector Sandbox Readiness Preview",
        description="Read-only preview.",
        category="readiness",
        allowed=True,
        dry_run_allowed=True,
        runtime_allowed=False,
        requires_review=True,
        requires_policy=True,
        requires_audit=True,
    )

    assert preview.allowed is True

    with pytest.raises(ValidationError):
        ConnectorSandboxCapabilityRule(
            rule_key="connector.sandbox.network.egress",
            title="Connector Sandbox Network Egress",
            description="Denied runtime capability.",
            category="network",
            allowed=True,
            dry_run_allowed=False,
            runtime_allowed=False,
            requires_review=True,
            requires_policy=True,
            requires_audit=True,
        )


def test_connector_sandbox_request_rejects_unsafe_metadata() -> None:
    request = ConnectorSandboxReadinessRequest(
        connector_key="mock.local.preview",
        owner_scope=["workspace:main"],
        requested_capabilities=["connector.sandbox.readiness.preview"],
    )

    assert request.connector_key == "mock.local.preview"

    with pytest.raises(ValidationError):
        ConnectorSandboxReadinessRequest(
            connector_key="Mock.Local",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        ConnectorSandboxReadinessRequest(
            connector_key="mock.local.preview",
            owner_scope=["workspace:main"],
            metadata={"external_url": "blocked"},
        )


def test_connector_sandbox_readiness_result_keeps_execution_disabled() -> None:
    result = ConnectorSandboxReadinessResult(
        connector_sandbox_readiness_id="connector-sandbox-readiness-test",
        connector_key="mock.local.preview",
        status="ready",
        sandbox_ready=True,
        runtime_execution_allowed=False,
        filesystem_access_allowed=False,
        network_access_allowed=False,
        credential_access_allowed=False,
        token_access_allowed=False,
        process_spawn_allowed=False,
        dynamic_import_allowed=False,
        package_install_allowed=False,
        connector_activation_allowed=False,
        audit_required=True,
        provenance_required=True,
        created_at=utc_now(),
    )

    assert result.sandbox_ready is True
    assert result.filesystem_access_allowed is False

    with pytest.raises(ValidationError):
        ConnectorSandboxReadinessResult(
            **result.model_copy(update={"runtime_execution_allowed": True}).model_dump()
        )
