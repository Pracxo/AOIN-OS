"""Decision assembly for dry-run action authorization."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.contracts.action_authorization import (
    ActionAuthorizationBlocker,
    DryRunActionAuthorizationDecision,
    DryRunActionAuthorizationRequest,
    utc_now,
)


def build_decision(
    request: DryRunActionAuthorizationRequest,
    *,
    policy_allowed: bool,
    role_allowed: bool,
    session_allowed: bool,
    blockers: list[ActionAuthorizationBlocker],
    warnings: list[dict[str, Any]] | None = None,
    required_policy_actions: list[str] | None = None,
    audit_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> DryRunActionAuthorizationDecision:
    """Build a non-executable decision from the evaluation result."""

    is_allowed = policy_allowed and role_allowed and session_allowed and not blockers
    decision = _decision_value(request.requested_operation, is_allowed, blockers)
    status = "allowed" if is_allowed else ("blocked" if blockers else "denied")
    reason = _reason(policy_allowed, role_allowed, session_allowed, blockers)
    return DryRunActionAuthorizationDecision(
        authorization_decision_id=f"action-authorization-decision-{uuid4().hex}",
        trace_id=request.trace_id,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        roles=request.roles,
        owner_scope=request.owner_scope,
        action_key=request.action_key,
        action_type=request.action_type,
        target_type=request.target_type,
        target_id=request.target_id,
        mode=request.mode,
        requested_operation=request.requested_operation,
        status=status,  # type: ignore[arg-type]
        decision=decision,  # type: ignore[arg-type]
        reason=reason,
        policy_allowed=policy_allowed,
        role_allowed=role_allowed,
        session_allowed=session_allowed,
        dry_run_only=True,
        write_allowed=False,
        execution_allowed=False,
        activation_allowed=False,
        external_calls_allowed=False,
        blockers=[item.model_dump(mode="json") for item in blockers],
        warnings=warnings or [],
        required_policy_actions=required_policy_actions or [],
        audit_refs=audit_refs or [],
        metadata=metadata or {},
        created_at=utc_now(),
    )


def _decision_value(
    requested_operation: str,
    is_allowed: bool,
    blockers: list[ActionAuthorizationBlocker],
) -> str:
    if blockers:
        if any(item.blocker_type == "unsupported_action" for item in blockers):
            return "unsupported"
        return "block"
    if not is_allowed:
        return "deny"
    if requested_operation == "review":
        return "allow_review_record"
    return "allow_dry_run_preview"


def _reason(
    policy_allowed: bool,
    role_allowed: bool,
    session_allowed: bool,
    blockers: list[ActionAuthorizationBlocker],
) -> str:
    if blockers:
        return blockers[0].reason
    if not role_allowed:
        return "role_denied"
    if not policy_allowed:
        return "policy_denied"
    if not session_allowed:
        return "session_denied"
    return "dry_run_authorization_allowed"


__all__ = ["build_decision"]
