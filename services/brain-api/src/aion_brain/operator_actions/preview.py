"""Governed operator action dry-run preview service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.action_authorization import (
    DryRunActionAuthorizationDecision,
    DryRunActionAuthorizationRequest,
)
from aion_brain.contracts.operator_actions import (
    OperatorActionBlocker,
    OperatorActionPreview,
    OperatorActionRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class OperatorActionPreviewService:
    """Create dry-run previews without executing or calling external systems."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        authorization_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._authorization_service = authorization_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> OperatorActionPreviewService:
        return OperatorActionPreviewService(
            self._repository,
            self._policy_adapter,
            authorization_service=self._authorization_service,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_preview(
        self,
        operator_action_request_id: str,
        scope: list[str],
        created_by: str | None = None,
    ) -> OperatorActionPreview:
        if self._settings is not None and not bool(
            getattr(self._settings, "operator_action_previews_enabled", True)
        ):
            raise RuntimeError("operator_action_previews_disabled")
        request = _require_request(self._repository, operator_action_request_id)
        if not _scope_matches(request.owner_scope, scope):
            raise ValueError("operator_action_request_not_found")
        authorization_decision = self._authorize_preview(request)
        authorize(
            self._policy_adapter,
            action_type="operator_action.preview.create",
            resource_type="operator_action_preview",
            resource_id=operator_action_request_id,
            scope=scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=request.risk_level,
            context={"would_execute": False},
        )
        blockers = _list_blockers(self._repository, request)
        authorization_blockers = (
            authorization_decision.blockers
            if authorization_decision is not None and authorization_decision.status != "allowed"
            else []
        )
        preview = OperatorActionPreview(
            operator_action_preview_id=f"operator-action-preview-{uuid4().hex}",
            trace_id=request.trace_id,
            operator_action_request_id=request.operator_action_request_id,
            status="blocked" if blockers or authorization_blockers else "created",
            preview_type="dry_run",
            owner_scope=request.owner_scope,
            expected_effects=[
                {
                    "effect": "record_operator_action_request",
                    "would_execute": False,
                    "target_type": request.target_type,
                }
            ],
            blocked_effects=[
                {"effect": "execute_action", "blocked": True, "reason": "execution_disabled"},
                {"effect": "external_call", "blocked": True, "reason": "external_calls_disabled"},
                {"effect": "activation", "blocked": True, "reason": "activation_disabled"},
            ],
            dry_run_result={
                "mode": "dry_run",
                "would_execute": False,
                "status": "blocked" if blockers or authorization_blockers else "previewed",
            },
            would_execute=False,
            execution_allowed=False,
            external_calls_allowed=False,
            activation_allowed=False,
            blockers=[
                *[blocker.model_dump(mode="json") for blocker in blockers],
                *authorization_blockers,
            ],
            warnings=[
                {
                    "code": "preview_only",
                    "message": "Operator action previews do not execute.",
                }
            ],
            metadata={
                "action_key": request.action_key,
                "dry_run_only": True,
                "dry_run_authz_decision": _decision_summary(authorization_decision),
            },
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save_preview = getattr(self._repository, "save_preview", None)
        stored = save_preview(preview) if callable(save_preview) else preview
        stored = stored if isinstance(stored, OperatorActionPreview) else preview
        save_request = getattr(self._repository, "save_request", None)
        if callable(save_request):
            save_request(
                request.model_copy(
                    update={
                        "preview_id": stored.operator_action_preview_id,
                        "status": "blocked"
                        if request.blocker_refs or authorization_blockers
                        else "previewed",
                    }
                )
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="operator_action_preview_created",
            node_type="operator_action_preview",
            node_id=stored.operator_action_preview_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            edge_from=request.operator_action_request_id,
            edge_to=stored.operator_action_preview_id,
            payload={
                "operator_action_request_id": request.operator_action_request_id,
                "would_execute": False,
                "status": stored.status,
            },
        )
        return stored

    def _authorize_preview(
        self,
        request: OperatorActionRequest,
    ) -> DryRunActionAuthorizationDecision | None:
        authorize_action = getattr(self._authorization_service, "authorize", None)
        if not callable(authorize_action):
            return None
        decision = authorize_action(
            DryRunActionAuthorizationRequest(
                authorization_request_id=f"authorization-preview-{request.operator_action_request_id}",
                trace_id=request.trace_id or self._actor_context.trace_id,
                actor_id=request.actor_id or self._actor_context.actor_id or "local.operator",
                workspace_id=request.workspace_id or self._actor_context.workspace_id or "local",
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
                operator_action_request_id=request.operator_action_request_id,
                metadata=request.metadata,
                created_by=self._actor_context.actor_id,
            )
        )
        return decision if isinstance(decision, DryRunActionAuthorizationDecision) else None

    def get_preview(
        self,
        operator_action_preview_id: str,
        scope: list[str],
    ) -> OperatorActionPreview | None:
        authorize(
            self._policy_adapter,
            action_type="operator_action.preview.read",
            resource_type="operator_action_preview",
            resource_id=operator_action_preview_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get_preview = getattr(self._repository, "get_preview", None)
        preview = get_preview(operator_action_preview_id) if callable(get_preview) else None
        if not isinstance(preview, OperatorActionPreview):
            return None
        return preview if _scope_matches(preview.owner_scope, scope) else None

    def list_previews(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionPreview]:
        authorize(
            self._policy_adapter,
            action_type="operator_action.preview.read",
            resource_type="operator_action_preview",
            resource_id=None,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_previews = getattr(self._repository, "list_previews", None)
        if not callable(list_previews):
            return []
        result = list_previews(scope=scope, status=status, limit=limit)
        return [item for item in result if isinstance(item, OperatorActionPreview)]


def _require_request(repository: object, operator_action_request_id: str) -> OperatorActionRequest:
    get = getattr(repository, "get_request", None)
    request = get(operator_action_request_id) if callable(get) else None
    if not isinstance(request, OperatorActionRequest):
        raise ValueError("operator_action_request_not_found")
    return request


def _list_blockers(
    repository: object,
    request: OperatorActionRequest,
) -> list[OperatorActionBlocker]:
    list_blockers = getattr(repository, "list_blockers", None)
    if not callable(list_blockers):
        return []
    result = list_blockers(
        scope=request.owner_scope,
        operator_action_request_id=request.operator_action_request_id,
        status="open",
        limit=100,
    )
    return [item for item in result if isinstance(item, OperatorActionBlocker)]


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


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


__all__ = ["OperatorActionPreviewService"]
