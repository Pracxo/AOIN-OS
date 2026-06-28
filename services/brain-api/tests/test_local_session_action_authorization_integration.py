from __future__ import annotations

from aion_brain.action_authorization import DryRunActionAuthorizationService
from aion_brain.contracts.action_authorization import DryRunActionAuthorizationRequest
from tests.operator_action_fakes import AllowPolicy


def test_local_session_boundary_blocks_action_authorization() -> None:
    service = DryRunActionAuthorizationService(policy_adapter=AllowPolicy())
    decision = service.authorize(
        DryRunActionAuthorizationRequest(
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
            action_key="operator.review",
            action_type="generic",
            target_type="generic",
            metadata={"local_session_context": {"session_valid": False}},
        )
    )

    assert decision.session_allowed is False
    assert decision.status == "blocked"
