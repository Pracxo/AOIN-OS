"""Policy helper for extension registry services."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest


def authorize_extension_action(
    policy_adapter: object,
    action_type: str,
    scope: list[str],
    *,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    trace_id: str | None = None,
    resource_type: str = "extension_package",
    resource_id: str | None = None,
    risk_level: str = "low",
    context: dict[str, Any] | None = None,
    approval_present: bool = True,
) -> None:
    """Authorize one generic Extension Registry action."""

    authorize = getattr(policy_adapter, "authorize", None)
    if not callable(authorize):
        raise AIONPolicyDeniedException("policy_adapter_unavailable")
    decision = authorize(
        PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=trace_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=approval_present,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
    )
    if not decision.allow:
        raise AIONPolicyDeniedException(decision.reason)


__all__ = ["authorize_extension_action"]
