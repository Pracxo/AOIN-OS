from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.connector_policy import (
    ConnectorAuthorizationMatrixEntry,
    ConnectorPolicyAction,
    ConnectorPolicyDryRunRequest,
    ConnectorPolicyDryRunResult,
    ConnectorPolicyTraceabilityRecord,
    utc_now,
)


def test_connector_policy_action_rejects_runtime_requirements() -> None:
    action = ConnectorPolicyAction(
        action_key="connector_policy.dry_run",
        title="Connector Policy Dry Run",
        description="Dry-run policy action only.",
        category="connector_policy",
        risk_level="medium",
        allowed_in_dry_run=True,
        allowed_in_runtime=False,
        requires_operator_review=True,
        requires_production_auth=False,
        requires_connector_runtime=False,
        requires_credentials=False,
        requires_external_call=False,
        requires_audit=True,
        requires_provenance=True,
    )

    assert action.allowed_in_runtime is False

    with pytest.raises(ValidationError):
        ConnectorPolicyAction(**action.model_copy(update={"allowed_in_runtime": True}).model_dump())


def test_connector_policy_request_rejects_unsafe_metadata() -> None:
    request = ConnectorPolicyDryRunRequest(
        connector_key="mock.local.preview",
        role="operator",
        requested_action_key="connector_policy.dry_run",
        owner_scope=["workspace:main"],
    )

    assert request.requested_action_key == "connector_policy.dry_run"

    with pytest.raises(ValidationError):
        ConnectorPolicyDryRunRequest(
            connector_key="Mock.Local",
            role="operator",
            requested_action_key="connector_policy.dry_run",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        ConnectorPolicyDryRunRequest(
            connector_key="mock.local.preview",
            role="operator",
            requested_action_key="connector_policy.dry_run",
            owner_scope=["workspace:main"],
            metadata={"external_url": "blocked"},
        )


def test_connector_policy_matrix_and_result_keep_runtime_blocked() -> None:
    matrix = ConnectorAuthorizationMatrixEntry(
        role="operator",
        action_key="connector_policy.dry_run",
        decision="allow_dry_run",
        reason="dry_run_preview",
        dry_run_allowed=True,
        runtime_allowed=False,
        external_call_allowed=False,
        credential_access_allowed=False,
        token_access_allowed=False,
        activation_allowed=False,
        review_required=True,
        audit_required=True,
    )
    result = ConnectorPolicyDryRunResult(
        connector_policy_dry_run_id="connector-policy-dry-run-test",
        connector_key="mock.local.preview",
        requested_action_key=matrix.action_key,
        role=matrix.role,
        decision=matrix.decision,
        dry_run_allowed=True,
        runtime_allowed=False,
        external_call_allowed=False,
        credential_access_allowed=False,
        token_access_allowed=False,
        activation_allowed=False,
        review_required=True,
        audit_required=True,
        provenance_required=True,
        created_at=utc_now(),
    )

    assert result.runtime_allowed is False

    with pytest.raises(ValidationError):
        ConnectorPolicyDryRunResult(
            **result.model_copy(update={"external_call_allowed": True}).model_dump()
        )


def test_connector_policy_traceability_record_is_safe() -> None:
    record = ConnectorPolicyTraceabilityRecord(
        traceability_id="traceability-1",
        connector_key="mock.local.preview",
        action_key="connector_policy.catalog.read",
        policy_refs=["docs/connectors/connector-policy-action-catalog.md"],
        status="ready",
        created_at=utc_now(),
    )

    assert record.status == "ready"

