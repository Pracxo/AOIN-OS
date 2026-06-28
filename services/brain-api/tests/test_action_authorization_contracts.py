from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.action_authorization import (
    ActionAuthorizationAuditResult,
    DryRunActionAuthorizationDecision,
    DryRunActionAuthorizationRequest,
    utc_now,
)


def _request(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "actor_id": "local.operator",
        "workspace_id": "local",
        "roles": ["operator"],
        "owner_scope": ["workspace:main"],
        "action_key": "operator.review",
        "action_type": "generic",
        "target_type": "generic",
    }
    payload.update(overrides)
    return payload


def test_authorization_request_rejects_non_dry_run_mode() -> None:
    with pytest.raises(ValidationError):
        DryRunActionAuthorizationRequest(**_request(mode="controlled"))


def test_decision_requires_disabled_privileged_paths() -> None:
    with pytest.raises(ValidationError):
        DryRunActionAuthorizationDecision(
            authorization_decision_id="decision-1",
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
            action_key="operator.review",
            action_type="generic",
            target_type="generic",
            mode="dry_run",
            requested_operation="preview",
            status="allowed",
            decision="allow_dry_run_preview",
            reason="allowed",
            policy_allowed=True,
            role_allowed=True,
            session_allowed=True,
            dry_run_only=True,
            write_allowed=True,
            execution_allowed=False,
            activation_allowed=False,
            external_calls_allowed=False,
            created_at=utc_now(),
        )


def test_audit_result_proves_disabled_boundaries() -> None:
    result = ActionAuthorizationAuditResult(
        action_authorization_audit_id="audit-1",
        status="passed",
        owner_scope=["workspace:main"],
        dry_run_only_enforced=True,
        write_blocked=True,
        execution_blocked=True,
        activation_blocked=True,
        external_calls_blocked=True,
        role_matrix_enforced=True,
        policy_enforced=True,
        session_boundary_enforced=True,
        created_at=utc_now(),
    )

    assert result.write_blocked is True
    assert result.execution_blocked is True
