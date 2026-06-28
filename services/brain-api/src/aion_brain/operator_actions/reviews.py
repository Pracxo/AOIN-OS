"""Governed operator action review service."""

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
    OperatorActionRequest,
    OperatorActionReview,
    OperatorActionReviewRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class OperatorActionReviewService:
    """Record reviews for dry-run operator action requests."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        authorization_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._authorization_service = authorization_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> OperatorActionReviewService:
        return OperatorActionReviewService(
            self._repository,
            self._policy_adapter,
            authorization_service=self._authorization_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def review(self, request: OperatorActionReviewRequest) -> OperatorActionReview:
        if self._settings is not None and not bool(
            getattr(self._settings, "operator_action_reviews_enabled", True)
        ):
            raise RuntimeError("operator_action_reviews_disabled")
        action_request = _require_request(self._repository, request.operator_action_request_id)
        authorization_decision = self._authorize_review(action_request, request)
        if authorization_decision is not None and authorization_decision.status != "allowed":
            raise PermissionError(authorization_decision.reason)
        authorize(
            self._policy_adapter,
            action_type="operator_action.review",
            resource_type="operator_action_request",
            resource_id=action_request.operator_action_request_id,
            scope=action_request.owner_scope,
            trace_id=action_request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=action_request.risk_level,
            approval_present=request.approval_present,
            context={"decision": request.decision, "execution_allowed": False},
        )
        blocker_refs = _blocker_refs(self._repository, action_request)
        review = OperatorActionReview(
            operator_action_review_id=f"operator-action-review-{uuid4().hex}",
            trace_id=action_request.trace_id,
            operator_action_request_id=action_request.operator_action_request_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            reviewer_id=request.reviewer_id,
            status="completed",
            decision=request.decision,
            reason=request.reason,
            approval_present=request.approval_present,
            execution_allowed=False,
            blocker_refs=blocker_refs,
            metadata={
                **request.metadata,
                "dry_run_authz_decision": _decision_summary(authorization_decision),
                "approval_does_not_execute": True,
                "dry_run_only": True,
            },
            created_by=request.actor_id or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save_review = getattr(self._repository, "save_review", None)
        stored = save_review(review) if callable(save_review) else review
        stored = stored if isinstance(stored, OperatorActionReview) else review
        save_request = getattr(self._repository, "save_request", None)
        if callable(save_request):
            save_request(
                action_request.model_copy(
                    update={
                        "status": "reviewed",
                        "review_id": stored.operator_action_review_id,
                        "reviewed_at": datetime.now(UTC),
                    }
                )
            )
        self._record_audit("operator_action_review_recorded", stored.operator_action_review_id)
        self._record_provenance(
            action_request.operator_action_request_id,
            stored.operator_action_review_id,
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="operator_action_review_recorded",
            node_type="operator_action_review",
            node_id=stored.operator_action_review_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            edge_from=action_request.operator_action_request_id,
            edge_to=stored.operator_action_review_id,
            payload={
                "decision": stored.decision,
                "execution_allowed": False,
                "approval_present": stored.approval_present,
            },
        )
        return stored

    def _authorize_review(
        self,
        action_request: OperatorActionRequest,
        review_request: OperatorActionReviewRequest,
    ) -> DryRunActionAuthorizationDecision | None:
        authorize_action = getattr(self._authorization_service, "authorize", None)
        if not callable(authorize_action):
            return None
        decision = authorize_action(
            DryRunActionAuthorizationRequest(
                authorization_request_id=f"authorization-review-{action_request.operator_action_request_id}",
                trace_id=action_request.trace_id or self._actor_context.trace_id,
                actor_id=(
                    review_request.actor_id
                    or self._actor_context.actor_id
                    or "local.reviewer"
                ),
                workspace_id=review_request.workspace_id
                or action_request.workspace_id
                or self._actor_context.workspace_id
                or "local",
                roles=_authorization_roles(review_request.metadata, default=["reviewer"]),
                owner_scope=action_request.owner_scope,
                action_key=action_request.action_key,
                action_type=action_request.action_type,
                target_type=action_request.target_type,
                target_id=action_request.target_id,
                mode=action_request.mode,
                requested_operation="review",
                local_auth_context_ref=_metadata_text(
                    review_request.metadata,
                    "local_auth_context_ref",
                ),
                local_session_preview_id=_metadata_text(
                    review_request.metadata,
                    "local_session_preview_id",
                ),
                operator_action_request_id=action_request.operator_action_request_id,
                metadata=review_request.metadata,
                created_by=review_request.actor_id or self._actor_context.actor_id,
            )
        )
        return decision if isinstance(decision, DryRunActionAuthorizationDecision) else None

    def list_reviews(
        self,
        scope: list[str],
        operator_action_request_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[OperatorActionReview]:
        authorize(
            self._policy_adapter,
            action_type="operator_action.review",
            resource_type="operator_action_review",
            resource_id=operator_action_request_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_reviews = getattr(self._repository, "list_reviews", None)
        if not callable(list_reviews):
            return []
        result = list_reviews(
            scope=scope,
            operator_action_request_id=operator_action_request_id,
            decision=decision,
            limit=limit,
        )
        return [item for item in result if isinstance(item, OperatorActionReview)]

    def _record_audit(self, event_type: str, review_id: str) -> None:
        for name in ("record_event", "record_audit_event"):
            record = getattr(self._audit_sink, name, None)
            if callable(record):
                try:
                    record({"event_type": event_type, "operator_action_review_id": review_id})
                    return
                except Exception:
                    return

    def _record_provenance(self, request_id: str, review_id: str) -> None:
        link = getattr(self._provenance_service, "record_link", None)
        if callable(link):
            try:
                link(request_id, review_id, "operator_action_reviewed")
            except Exception:
                return


def _require_request(repository: object, operator_action_request_id: str) -> OperatorActionRequest:
    get = getattr(repository, "get_request", None)
    request = get(operator_action_request_id) if callable(get) else None
    if not isinstance(request, OperatorActionRequest):
        raise ValueError("operator_action_request_not_found")
    return request


def _blocker_refs(repository: object, request: OperatorActionRequest) -> list[str]:
    list_blockers = getattr(repository, "list_blockers", None)
    if not callable(list_blockers):
        return request.blocker_refs
    result = list_blockers(
        scope=request.owner_scope,
        operator_action_request_id=request.operator_action_request_id,
        limit=100,
    )
    refs = [
        item.operator_action_blocker_id
        for item in result
        if isinstance(item, OperatorActionBlocker) and item.status == "open"
    ]
    return sorted(set([*request.blocker_refs, *refs]))


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


__all__ = ["OperatorActionReviewService"]
