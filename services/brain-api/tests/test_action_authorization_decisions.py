from __future__ import annotations

from aion_brain.action_authorization.decisions import build_decision
from aion_brain.contracts.action_authorization import DryRunActionAuthorizationRequest


def test_action_authorization_decision_allows_dry_run_preview_only() -> None:
    request = DryRunActionAuthorizationRequest(
        actor_id="local.operator",
        workspace_id="local",
        roles=["operator"],
        owner_scope=["workspace:main"],
        action_key="operator.review",
        action_type="generic",
        target_type="generic",
    )

    decision = build_decision(
        request,
        policy_allowed=True,
        role_allowed=True,
        session_allowed=True,
        blockers=[],
    )

    assert decision.decision == "allow_dry_run_preview"
    assert decision.dry_run_only is True
    assert decision.write_allowed is False
    assert decision.execution_allowed is False
    assert decision.activation_allowed is False
    assert decision.external_calls_allowed is False
