"""Governed operator action request service."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.action_authorization import (
    DryRunActionAuthorizationDecision,
    DryRunActionAuthorizationRequest,
)
from aion_brain.contracts.operator_actions import (
    OperatorActionBlocker,
    OperatorActionCreateRequest,
    OperatorActionRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.operator_actions.redaction import redact_operator_action_payload


class OperatorActionRequestService:
    """Create and query dry-run operator action request records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        blocker_service: object | None = None,
        preview_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        authorization_service: object | None = None,
        notification_router: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._blocker_service = blocker_service
        self._preview_service = preview_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._authorization_service = authorization_service
        self._notification_router = notification_router
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def set_preview_service(self, preview_service: object) -> None:
        self._preview_service = preview_service

    def set_notification_router(self, notification_router: object) -> None:
        self._notification_router = notification_router

    def with_actor_context(self, actor_context: ActorContext) -> OperatorActionRequestService:
        return OperatorActionRequestService(
            self._repository,
            self._policy_adapter,
            blocker_service=self._blocker_service,
            preview_service=self._preview_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            authorization_service=self._authorization_service,
            notification_router=self._notification_router,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_request(self, request: OperatorActionCreateRequest) -> OperatorActionRequest:
        if self._settings is not None and not bool(
            getattr(self._settings, "operator_actions_enabled", True)
        ):
            raise RuntimeError("operator_actions_disabled")
        if request.mode != "dry_run":
            raise ValueError("operator_actions_are_dry_run_only")
        redacted_payload, findings = redact_operator_action_payload(request.request_payload)
        request_id = request.operator_action_request_id or f"operator-action-request-{uuid4().hex}"
        authorization_decision = self._authorize_dry_run_request(
            request,
            request_id,
            findings,
        )
        if authorization_decision is not None and authorization_decision.status != "allowed":
            return self._create_blocked_authorization_request(
                request,
                request_id,
                redacted_payload,
                findings,
                authorization_decision,
            )
        authorize(
            self._policy_adapter,
            action_type="operator_action.request.create",
            resource_type="operator_action_request",
            resource_id=request_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=request.risk_level,
            context={"mode": request.mode, "action_key": request.action_key},
        )
        blockers = self._create_initial_blockers(request_id, request, findings)
        now = datetime.now(UTC)
        stored = _save_request(
            self._repository,
            OperatorActionRequest(
                operator_action_request_id=request_id,
                trace_id=request.trace_id or self._actor_context.trace_id,
                actor_id=request.actor_id or self._actor_context.actor_id,
                workspace_id=request.workspace_id or self._actor_context.workspace_id,
                action_key=request.action_key,
                action_type=request.action_type,
                target_type=request.target_type,
                target_id=request.target_id,
                status="blocked" if blockers else "requested",
                mode="dry_run",
                risk_level=request.risk_level,
                owner_scope=request.owner_scope,
                request_payload_hash=_payload_hash(redacted_payload),
                redacted_request_payload=redacted_payload,
                required_policy_actions=request.required_policy_actions,
                required_approvals=request.required_approvals,
                required_evidence_refs=request.required_evidence_refs,
                blocker_refs=[blocker.operator_action_blocker_id for blocker in blockers],
                preview_id=None,
                review_id=None,
                execution_allowed=False,
                external_calls_allowed=False,
                activation_allowed=False,
                metadata={
                    **request.metadata,
                    "redaction_findings": findings,
                    "dry_run_authz_decision": _decision_summary(authorization_decision),
                    "create_notifications_requested": request.create_notifications,
                    "dry_run_only": True,
                },
                created_by=request.created_by or self._actor_context.actor_id,
                created_at=now,
            ),
        )
        if request.create_preview and bool(
            getattr(self._settings, "operator_action_previews_enabled", True)
        ):
            create_preview = getattr(self._preview_service, "create_preview", None)
            if callable(create_preview):
                preview = create_preview(
                    stored.operator_action_request_id,
                    stored.owner_scope,
                    created_by=stored.created_by,
                )
                stored = _save_request(
                    self._repository,
                    stored.model_copy(
                        update={
                            "preview_id": getattr(preview, "operator_action_preview_id", None),
                            "status": "blocked" if stored.blocker_refs else "previewed",
                        }
                    ),
                )
        self._record_audit("operator_action_request_created", stored.operator_action_request_id)
        self._record_provenance(stored.operator_action_request_id)
        self._maybe_notify(stored, request.create_notifications)
        emit_telemetry(
            self._telemetry_service,
            event_type="operator_action_request_created",
            node_type="operator_action_request",
            node_id=stored.operator_action_request_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={
                "status": stored.status,
                "action_key": stored.action_key,
                "mode": stored.mode,
                "execution_allowed": False,
            },
        )
        return stored

    def _authorize_dry_run_request(
        self,
        request: OperatorActionCreateRequest,
        request_id: str,
        findings: list[dict[str, Any]],
    ) -> DryRunActionAuthorizationDecision | None:
        authorize_action = getattr(self._authorization_service, "authorize", None)
        if not callable(authorize_action):
            return None
        decision = authorize_action(
            DryRunActionAuthorizationRequest(
                authorization_request_id=f"authorization-{request_id}",
                trace_id=request.trace_id or self._actor_context.trace_id,
                actor_id=request.actor_id or self._actor_context.actor_id or "local.operator",
                workspace_id=request.workspace_id
                or self._actor_context.workspace_id
                or "local",
                roles=_authorization_roles(request.metadata, default=["operator"]),
                owner_scope=request.owner_scope,
                action_key=request.action_key,
                action_type=request.action_type,
                target_type=request.target_type,
                target_id=request.target_id,
                mode=request.mode,
                requested_operation="preview",
                local_auth_context_ref=_metadata_text(request.metadata, "local_auth_context_ref"),
                local_session_preview_id=_metadata_text(
                    request.metadata,
                    "local_session_preview_id",
                ),
                operator_action_request_id=request_id,
                metadata={
                    **request.metadata,
                    "request_payload_findings": findings,
                    "operator_action_request_id": request_id,
                },
                created_by=request.created_by or self._actor_context.actor_id,
            )
        )
        return decision if isinstance(decision, DryRunActionAuthorizationDecision) else None

    def _create_blocked_authorization_request(
        self,
        request: OperatorActionCreateRequest,
        request_id: str,
        redacted_payload: dict[str, Any],
        findings: list[dict[str, Any]],
        decision: DryRunActionAuthorizationDecision,
    ) -> OperatorActionRequest:
        blockers = self._create_initial_blockers(request_id, request, findings)
        blockers.extend(self._authorization_blockers(request_id, request, decision))
        stored = _save_request(
            self._repository,
            OperatorActionRequest(
                operator_action_request_id=request_id,
                trace_id=request.trace_id or self._actor_context.trace_id,
                actor_id=request.actor_id or self._actor_context.actor_id,
                workspace_id=request.workspace_id or self._actor_context.workspace_id,
                action_key=request.action_key,
                action_type=request.action_type,
                target_type=request.target_type,
                target_id=request.target_id,
                status="blocked",
                mode="dry_run",
                risk_level=request.risk_level,
                owner_scope=request.owner_scope,
                request_payload_hash=_payload_hash(redacted_payload),
                redacted_request_payload=redacted_payload,
                required_policy_actions=sorted(
                    set([*request.required_policy_actions, *decision.required_policy_actions])
                ),
                required_approvals=request.required_approvals,
                required_evidence_refs=request.required_evidence_refs,
                blocker_refs=[blocker.operator_action_blocker_id for blocker in blockers],
                preview_id=None,
                review_id=None,
                execution_allowed=False,
                external_calls_allowed=False,
                activation_allowed=False,
                metadata={
                    **request.metadata,
                    "redaction_findings": findings,
                    "dry_run_authz_decision": _decision_summary(decision),
                    "dry_run_only": True,
                },
                created_by=request.created_by or self._actor_context.actor_id,
                created_at=datetime.now(UTC),
            ),
        )
        self._record_audit(
            "operator_action_request_authorization_blocked",
            stored.operator_action_request_id,
        )
        return stored

    def _authorization_blockers(
        self,
        request_id: str,
        request: OperatorActionCreateRequest,
        decision: DryRunActionAuthorizationDecision,
    ) -> list[OperatorActionBlocker]:
        blockers: list[OperatorActionBlocker] = []
        for item in decision.blockers:
            blocker_type = _operator_blocker_type(str(item.get("blocker_type") or "generic"))
            blocker_record = self._create_blocker(
                request_id=request_id,
                request=request,
                blocker_type=blocker_type,
                severity=str(item.get("severity") or "high"),
                reason=str(item.get("reason") or "authorization_denied"),
                recommended_action="Resolve dry-run authorization blockers before preview.",
                metadata={"authz_blocker_type": item.get("blocker_type")},
            )
            if isinstance(blocker_record, OperatorActionBlocker):
                blockers.append(blocker_record)
        return blockers

    def get_request(
        self,
        operator_action_request_id: str,
        scope: list[str],
    ) -> OperatorActionRequest | None:
        authorize(
            self._policy_adapter,
            action_type="operator_action.request.read",
            resource_type="operator_action_request",
            resource_id=operator_action_request_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get_request = getattr(self._repository, "get_request", None)
        request = get_request(operator_action_request_id) if callable(get_request) else None
        if not isinstance(request, OperatorActionRequest):
            return None
        if not _scope_matches(request.owner_scope, scope):
            return None
        return request

    def list_requests(
        self,
        scope: list[str],
        status: str | None = None,
        action_type: str | None = None,
        target_type: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionRequest]:
        authorize(
            self._policy_adapter,
            action_type="operator_action.request.read",
            resource_type="operator_action_request",
            resource_id=None,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_requests = getattr(self._repository, "list_requests", None)
        if not callable(list_requests):
            return []
        result = list_requests(
            scope=scope,
            status=status,
            action_type=action_type,
            target_type=target_type,
            limit=limit,
        )
        return [item for item in result if isinstance(item, OperatorActionRequest)]

    def archive_request(
        self,
        operator_action_request_id: str,
        actor_id: str | None,
        reason: str,
    ) -> OperatorActionRequest:
        request = _require_request(self._repository, operator_action_request_id)
        authorize(
            self._policy_adapter,
            action_type="operator_action.request.update",
            resource_type="operator_action_request",
            resource_id=operator_action_request_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context={"reason": reason},
        )
        archived = request.model_copy(
            update={
                "status": "archived",
                "archived_at": datetime.now(UTC),
                "metadata": {**request.metadata, "archive_reason": reason},
            }
        )
        return _save_request(self._repository, archived)

    def _create_initial_blockers(
        self,
        request_id: str,
        request: OperatorActionCreateRequest,
        findings: list[dict[str, Any]],
    ) -> list[OperatorActionBlocker]:
        blockers: list[OperatorActionBlocker] = []
        for blocker_type, reason in (
            ("execution_disabled", "operator_action_execution_disabled"),
            ("external_calls_disabled", "operator_action_external_calls_disabled"),
            ("activation_disabled", "operator_action_activation_disabled"),
        ):
            blocker = self._create_blocker(
                request_id=request_id,
                request=request,
                blocker_type=blocker_type,
                severity="critical",
                reason=reason,
                recommended_action="Review dry-run preview only.",
            )
            if isinstance(blocker, OperatorActionBlocker):
                blockers.append(blocker)
        for policy_action in request.required_policy_actions:
            blocker = self._create_blocker(
                request_id=request_id,
                request=request,
                blocker_type="policy_required",
                severity="medium",
                reason=f"policy_required:{policy_action}",
                recommended_action="Review required policy decision before future write support.",
            )
            if isinstance(blocker, OperatorActionBlocker):
                blockers.append(blocker)
        for approval in request.required_approvals:
            blocker = self._create_blocker(
                request_id=request_id,
                request=request,
                blocker_type="approval_required",
                severity=request.risk_level,
                reason=f"approval_required:{approval}",
                recommended_action="Record review only; approval does not execute.",
            )
            if isinstance(blocker, OperatorActionBlocker):
                blockers.append(blocker)
        for finding in findings:
            blocker_type = _blocker_type_for_finding(finding)
            blocker = self._create_blocker(
                request_id=request_id,
                request=request,
                blocker_type=blocker_type,
                severity=str(finding.get("severity") or "high"),
                reason=str(finding.get("code") or "unsafe_payload"),
                recommended_action="Use the redacted request payload for review.",
                metadata={"finding": finding},
            )
            if isinstance(blocker, OperatorActionBlocker):
                blockers.append(blocker)
        return blockers

    def _create_blocker(
        self,
        *,
        request_id: str,
        request: OperatorActionCreateRequest,
        blocker_type: str,
        severity: str,
        reason: str,
        recommended_action: str,
        metadata: dict[str, Any] | None = None,
    ) -> object:
        create = getattr(self._blocker_service, "create_blocker", None)
        if not callable(create):
            return OperatorActionBlocker(
                operator_action_blocker_id=f"operator-action-blocker-{uuid4().hex}",
                trace_id=request.trace_id or self._actor_context.trace_id,
                operator_action_request_id=request_id,
                blocker_type=blocker_type,  # type: ignore[arg-type]
                severity=severity,  # type: ignore[arg-type]
                status="open",
                reason=reason,
                recommended_action=recommended_action,
                source_type=request.target_type,
                source_id=request.target_id,
                metadata={"action_key": request.action_key, **(metadata or {})},
                created_at=datetime.now(UTC),
            )
        return create(
            operator_action_request_id=request_id,
            trace_id=request.trace_id or self._actor_context.trace_id,
            blocker_type=blocker_type,
            severity=severity,
            reason=reason,
            recommended_action=recommended_action,
            source_type=request.target_type,
            source_id=request.target_id,
            metadata={"action_key": request.action_key, **(metadata or {})},
        )

    def _record_audit(self, event_type: str, request_id: str) -> None:
        for name in ("record_event", "record_audit_event"):
            record = getattr(self._audit_sink, name, None)
            if callable(record):
                try:
                    record({"event_type": event_type, "operator_action_request_id": request_id})
                    return
                except Exception:
                    return

    def _record_provenance(self, request_id: str) -> None:
        link = getattr(self._provenance_service, "record_link", None)
        if callable(link):
            try:
                link(request_id, request_id, "operator_action_request_recorded")
            except Exception:
                return

    def _maybe_notify(self, request: OperatorActionRequest, requested: bool) -> None:
        enabled_by_default = bool(
            getattr(self._settings, "operator_action_create_notifications_default", False)
        )
        if not (requested or enabled_by_default):
            return
        publish = getattr(self._notification_router, "publish_local", None)
        if callable(publish):
            try:
                publish(
                    {
                        "event_type": "operator_action_request_created",
                        "operator_action_request_id": request.operator_action_request_id,
                    }
                )
            except Exception:
                return


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _blocker_type_for_finding(finding: dict[str, Any]) -> str:
    code = str(finding.get("code") or "")
    if "prompt" in code:
        return "raw_prompt_detected"
    if "reasoning" in code:
        return "hidden_reasoning_detected"
    if "secret" in code:
        return "secret_detected"
    return "unsafe_payload"


def _operator_blocker_type(blocker_type: str) -> str:
    if blocker_type in {
        "unsupported_action",
        "unsafe_payload",
        "raw_prompt_detected",
        "hidden_reasoning_detected",
        "secret_detected",
    }:
        return blocker_type
    if blocker_type in {"write_blocked", "execution_blocked"}:
        return "execution_disabled"
    if blocker_type == "activation_blocked":
        return "activation_disabled"
    if blocker_type == "external_calls_blocked":
        return "external_calls_disabled"
    return "policy_required"


def _authorization_roles(metadata: dict[str, Any], *, default: list[str]) -> list[str]:
    for key in ("roles", "local_roles", "local_auth_roles"):
        roles = metadata.get(key)
        if isinstance(roles, list):
            cleaned = [str(role) for role in roles if str(role).strip()]
            if cleaned:
                return cleaned
    return default


def _metadata_text(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return str(value) if isinstance(value, str) and value else None


def _decision_summary(
    decision: DryRunActionAuthorizationDecision | None,
) -> dict[str, Any] | None:
    if decision is None:
        return None
    return {
        "authz_decision_id": decision.authorization_decision_id,
        "status": decision.status,
        "decision": decision.decision,
        "reason": decision.reason,
        "policy_allowed": decision.policy_allowed,
        "role_allowed": decision.role_allowed,
        "session_allowed": decision.session_allowed,
        "dry_run_only": decision.dry_run_only,
        "write_allowed": False,
        "execution_allowed": False,
        "activation_allowed": False,
        "external_calls_allowed": False,
    }


def _require_request(repository: object, operator_action_request_id: str) -> OperatorActionRequest:
    get = getattr(repository, "get_request", None)
    request = get(operator_action_request_id) if callable(get) else None
    if not isinstance(request, OperatorActionRequest):
        raise ValueError("operator_action_request_not_found")
    return request


def _save_request(repository: object, request: OperatorActionRequest) -> OperatorActionRequest:
    save = getattr(repository, "save_request", None)
    stored = save(request) if callable(save) else request
    return stored if isinstance(stored, OperatorActionRequest) else request


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["OperatorActionRequestService"]
