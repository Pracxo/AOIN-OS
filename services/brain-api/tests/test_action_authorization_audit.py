from __future__ import annotations

from aion_brain.action_authorization import ActionAuthorizationAuditService
from aion_brain.contracts.action_authorization import ActionAuthorizationAuditRequest


def test_action_authorization_audit_confirms_privileged_paths_blocked() -> None:
    result = ActionAuthorizationAuditService().audit(
        ActionAuthorizationAuditRequest(owner_scope=["workspace:main"])
    )

    assert result.status == "passed"
    assert result.dry_run_only_enforced is True
    assert result.write_blocked is True
    assert result.execution_blocked is True
    assert result.activation_blocked is True
    assert result.external_calls_blocked is True
    assert result.role_matrix_enforced is True
    assert result.policy_enforced is True
    assert result.session_boundary_enforced is True
