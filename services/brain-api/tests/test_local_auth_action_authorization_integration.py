from __future__ import annotations

from aion_brain.action_authorization import DryRunActionAuthorizationService
from aion_brain.contracts.action_authorization import DryRunActionAuthorizationRequest
from tests.operator_action_fakes import AllowPolicy


def test_local_auth_roles_drive_action_authorization() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())
    decision = service.authorize(
        DryRunActionAuthorizationRequest(
            actor_id="local.viewer",
            workspace_id="local",
            roles=["viewer"],
            owner_scope=["workspace:main"],
            action_key="operator.review",
            action_type="generic",
            target_type="generic",
        )
    )

    assert decision.role_allowed is False
    assert decision.execution_allowed is False
