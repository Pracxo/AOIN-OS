from __future__ import annotations

from aion_brain.action_authorization import DryRunActionAuthorizationService
from aion_brain.contracts.action_authorization import DryRunActionAuthorizationRequest
from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService
from tests.operator_action_fakes import AllowPolicy


def test_role_matrix_is_enforced_by_action_authorization() -> None:
    matrix = RolePermissionMatrixService().build_permission_matrix()
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())

    assert matrix["roles"]["operator"]["dry_run_actions"]
    assert service.authorize(
        DryRunActionAuthorizationRequest(
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
            action_key="operator.review",
            action_type="generic",
            target_type="generic",
        )
    ).role_allowed is True
    assert service.authorize(
        DryRunActionAuthorizationRequest(
            actor_id="local.auditor",
            workspace_id="local",
            roles=["auditor"],
            owner_scope=["workspace:main"],
            action_key="operator.review",
            action_type="generic",
            target_type="generic",
        )
    ).role_allowed is False
