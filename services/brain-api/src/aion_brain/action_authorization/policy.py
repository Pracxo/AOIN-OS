"""Policy adapter integration for dry-run action authorization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest

DRY_RUN_AUTHORIZE_ACTION = "action_authorization.dry_run.authorize"
AUDIT_ACTION = "action_authorization.audit.run"
DECISION_READ_ACTION = "action_authorization.decision.read"


@dataclass(frozen=True)
class PolicyCheckResult:
    """Normalized policy result for authorization decisions."""

    allowed: bool
    reason: str
    decision_id: str | None


class ActionAuthorizationPolicyChecker:
    """Call the policy adapter without raising on ordinary denial."""

    def __init__(self, policy_adapter: object | None) -> None:
        self._policy_adapter = policy_adapter

    def check(
        self,
        *,
        action_type: str,
        actor_id: str,
        workspace_id: str,
        owner_scope: list[str],
        trace_id: str | None,
        context: dict[str, Any],
    ) -> PolicyCheckResult:
        """Return a fail-closed policy decision."""

        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return PolicyCheckResult(False, "policy_adapter_unavailable", None)
        decision = authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="action_authorization",
                resource_id=None,
                risk_level="medium",
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=owner_scope,
                context=context,
            )
        )
        if not isinstance(decision, PolicyDecision):
            return PolicyCheckResult(False, "policy_adapter_returned_invalid_decision", None)
        return PolicyCheckResult(decision.allow, decision.reason, decision.decision_id)


__all__ = [
    "AUDIT_ACTION",
    "DECISION_READ_ACTION",
    "DRY_RUN_AUTHORIZE_ACTION",
    "ActionAuthorizationPolicyChecker",
    "PolicyCheckResult",
]
