"""Dry-run action authorization evaluator."""

from __future__ import annotations

from typing import Any, get_args

from aion_brain.action_authorization.blockers import blocker, blockers_for_findings
from aion_brain.action_authorization.decisions import build_decision
from aion_brain.action_authorization.policy import (
    DRY_RUN_AUTHORIZE_ACTION,
    ActionAuthorizationPolicyChecker,
)
from aion_brain.action_authorization.redaction import (
    payload_findings,
    redact_authorization_payload,
)
from aion_brain.contracts.action_authorization import (
    ActionAuthorizationBlocker,
    DryRunActionAuthorizationDecision,
    DryRunActionAuthorizationRequest,
)
from aion_brain.contracts.operator_actions import (
    OperatorActionTargetType,
    OperatorActionType,
)
from aion_brain.dialogue._shared import emit_telemetry
from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService

ALLOWED_ACTION_TYPES = set(get_args(OperatorActionType))
ALLOWED_TARGET_TYPES = set(get_args(OperatorActionTargetType))
PREVIEW_OPERATIONS = {"request", "preview"}
REVIEW_OPERATIONS = {"review", "review_record"}


class DryRunActionAuthorizationService:
    """Authorize dry-run previews and review records without granting execution."""

    def __init__(
        self,
        *,
        matrix_service: RolePermissionMatrixService | None = None,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._matrix_service = matrix_service or RolePermissionMatrixService()
        self._policy_checker = ActionAuthorizationPolicyChecker(policy_adapter)
        self._telemetry_service = telemetry_service
        self._settings = settings

    def authorize(
        self,
        request: DryRunActionAuthorizationRequest,
    ) -> DryRunActionAuthorizationDecision:
        """Return a visible authorization decision for dry-run-only operations."""

        redaction_findings = [
            *payload_findings(request.metadata),
            *_operator_payload_findings(request.metadata),
        ]
        redacted_metadata = redact_authorization_payload(request.metadata)
        metadata = redacted_metadata if isinstance(redacted_metadata, dict) else {}
        blockers = blockers_for_findings(
            redaction_findings,
            trace_id=request.trace_id,
            source_id=request.authorization_request_id,
        )
        blockers.extend(self._boundary_blockers(request))
        role_allowed = self._role_allowed(request)
        if not role_allowed:
            blockers.append(
                blocker(
                    "role_denied",
                    "role_denied",
                    trace_id=request.trace_id,
                    source_type="role_matrix",
                    source_id=request.operator_action_request_id,
                    recommended_action="Use a role with explicit dry-run or review permission.",
                )
            )
        session_allowed = _session_allowed(metadata)
        if not session_allowed:
            blockers.append(
                blocker(
                    "session_denied",
                    "session_denied",
                    trace_id=request.trace_id,
                    source_type="local_session",
                    source_id=request.local_session_preview_id,
                    recommended_action="Use a valid read-only local session preview.",
                )
            )
        policy_check = self._policy_checker.check(
            action_type=DRY_RUN_AUTHORIZE_ACTION,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            trace_id=request.trace_id,
            context={
                "mode": request.mode,
                "requested_operation": request.requested_operation,
                "action_key": request.action_key,
                "action_type": request.action_type,
                "target_type": request.target_type,
                "roles": request.roles,
                "dry_run_only": True,
                "write_allowed": False,
                "execution_allowed": False,
                "activation_allowed": False,
                "external_calls_allowed": False,
            },
        )
        if not policy_check.allowed:
            blockers.append(
                blocker(
                    "policy_denied",
                    "policy_denied",
                    trace_id=request.trace_id,
                    source_type="policy",
                    source_id=policy_check.decision_id,
                    recommended_action="Inspect policy decision before retrying.",
                    metadata={"policy_reason": policy_check.reason},
                )
            )
        decision = build_decision(
            request,
            policy_allowed=policy_check.allowed,
            role_allowed=role_allowed,
            session_allowed=session_allowed,
            blockers=blockers,
            warnings=self._warnings(metadata),
            required_policy_actions=[DRY_RUN_AUTHORIZE_ACTION],
            audit_refs=[policy_check.decision_id] if policy_check.decision_id else [],
            metadata={
                "redaction_findings": [
                    {"finding": _metadata_finding_code(item)}
                    for item in redaction_findings
                ],
                "policy_reason": policy_check.reason,
                "role_matrix_version": "aion-097",
                "operator_action_request_id": request.operator_action_request_id,
            },
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="dry_run_action_authorization_decided",
            node_type="action_authorization_decision",
            node_id=decision.authorization_decision_id,
            intensity=0.95 if decision.status != "allowed" else 0.7,
            trace_id=decision.trace_id,
            edge_from=request.operator_action_request_id,
            edge_to=decision.authorization_decision_id,
            payload={
                "decision": decision.decision,
                "status": decision.status,
                "write_allowed": False,
                "execution_allowed": False,
                "activation_allowed": False,
                "external_calls_allowed": False,
            },
        )
        return decision

    def _boundary_blockers(
        self,
        request: DryRunActionAuthorizationRequest,
    ) -> list[ActionAuthorizationBlocker]:
        blockers: list[ActionAuthorizationBlocker] = []
        if request.mode != "dry_run":
            blockers.append(
                blocker(
                    "non_dry_run_mode",
                    "non_dry_run_mode",
                    trace_id=request.trace_id,
                    severity="critical",
                    recommended_action="Request dry_run mode only.",
                )
            )
        if request.action_type not in ALLOWED_ACTION_TYPES:
            blockers.append(
                blocker(
                    "unsupported_action",
                    "unsupported_action_type",
                    trace_id=request.trace_id,
                    recommended_action="Use a supported dry-run operator action type.",
                )
            )
        if request.target_type not in ALLOWED_TARGET_TYPES:
            blockers.append(
                blocker(
                    "unsupported_action",
                    "unsupported_target_type",
                    trace_id=request.trace_id,
                    recommended_action="Use a supported operator action target type.",
                )
            )
        for flag, blocker_type, reason in (
            ("action_authorization_write_allowed", "write_blocked", "write_blocked"),
            (
                "action_authorization_execution_allowed",
                "execution_blocked",
                "execution_blocked",
            ),
            (
                "action_authorization_activation_allowed",
                "activation_blocked",
                "activation_blocked",
            ),
            (
                "action_authorization_external_calls_allowed",
                "external_calls_blocked",
                "external_calls_blocked",
            ),
        ):
            if bool(getattr(self._settings, flag, False)):
                blockers.append(
                    blocker(
                        blocker_type,
                        reason,
                        trace_id=request.trace_id,
                        severity="critical",
                        recommended_action="Keep action authorization privileged flags disabled.",
                    )
                )
        return blockers

    def _role_allowed(self, request: DryRunActionAuthorizationRequest) -> bool:
        if not request.roles:
            return False
        matrix = self._matrix_service.build_permission_matrix()
        role_entries = matrix.get("roles", {})
        if not isinstance(role_entries, dict):
            return False
        if request.requested_operation in REVIEW_OPERATIONS:
            return any(
                isinstance(role_entries.get(role), dict)
                and bool(role_entries[role].get("review_actions"))
                for role in request.roles
            )
        if request.requested_operation in PREVIEW_OPERATIONS:
            return any(
                isinstance(role_entries.get(role), dict)
                and bool(role_entries[role].get("dry_run_actions"))
                for role in request.roles
            )
        return False

    def _warnings(self, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        if metadata.get("authz_demo") is True:
            warnings.append({"code": "static_demo", "message": "Static demo decision only."})
        return warnings


def _session_allowed(metadata: dict[str, Any]) -> bool:
    if metadata.get("session_allowed") is False:
        return False
    for key in ("local_session_context", "session_context", "local_session"):
        session = metadata.get(key)
        if isinstance(session, dict):
            if session.get("session_valid") is False:
                return False
            if session.get("session_read_only") is False:
                return False
            if session.get("write_allowed") is True:
                return False
            if session.get("execute_allowed") is True:
                return False
            if session.get("activation_allowed") is True:
                return False
            if session.get("external_calls_allowed") is True:
                return False
    return True


def _metadata_finding_code(finding: dict[str, Any]) -> str:
    code = str(finding.get("finding") or "unsafe_payload")
    return {
        "raw_prompt_detected": "unsafe_payload_text",
        "hidden_reasoning_detected": "unsafe_reasoning_material",
        "secret_detected": "protected_material",
    }.get(code, "unsafe_payload")


def _operator_payload_findings(metadata: dict[str, Any]) -> list[dict[str, object]]:
    findings = metadata.get("request_payload_findings")
    if not isinstance(findings, list):
        return []
    mapped: list[dict[str, object]] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or item.get("finding") or "unsafe_payload")
        if "prompt" in code:
            mapped.append({"finding": "raw_prompt_detected"})
        elif "reasoning" in code:
            mapped.append({"finding": "hidden_reasoning_detected"})
        elif "secret" in code:
            mapped.append({"finding": "secret_detected"})
        else:
            mapped.append({"finding": "unsafe_payload"})
    return mapped


__all__ = ["DryRunActionAuthorizationService"]
