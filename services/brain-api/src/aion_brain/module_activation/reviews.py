"""Activation review service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.module_activation import (
    ActivationReview,
    ActivationReviewRequest,
    ActivationReviewStatus,
)
from aion_brain.module_activation.policy import authorize_module_activation_action
from aion_brain.module_activation.redaction import redact_activation_payload
from aion_brain.module_activation.repository import ModuleActivationRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ActivationReviewService:
    """Record human/operator review without enabling activation."""

    def __init__(
        self,
        repository: ModuleActivationRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def review(self, request: ActivationReviewRequest, scope: list[str]) -> ActivationReview:
        if not self._settings.module_activation_reviews_enabled:
            raise RuntimeError("module_activation_reviews_disabled")
        activation_request = self._repository.get_request(request.activation_request_id)
        if activation_request is None or not _in_scope(activation_request.owner_scope, scope):
            raise AIONNotFoundException("module_activation_request_not_found")
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.review.create",
            scope,
            actor_id=request.actor_id or activation_request.actor_id,
            workspace_id=request.workspace_id or activation_request.workspace_id,
            trace_id=activation_request.trace_id,
            resource_type="module_activation_review",
            resource_id=request.activation_request_id,
            risk_level=activation_request.risk_level,
            approval_present=request.approval_present,
            context={"decision": request.decision, "activation_allowed": False},
        )
        review = ActivationReview(
            activation_review_id=f"activation-review-{uuid4().hex}",
            trace_id=activation_request.trace_id,
            activation_request_id=request.activation_request_id,
            actor_id=request.actor_id or activation_request.actor_id,
            workspace_id=request.workspace_id or activation_request.workspace_id,
            status=_review_status(request.decision),
            decision=request.decision,
            reviewer_id=request.reviewer_id or request.actor_id,
            reason=request.reason,
            approval_request_id=None,
            policy_decision_id=None,
            blocker_refs=activation_request.blocker_refs,
            metadata=redact_activation_payload(
                {
                    **request.metadata,
                    "activation_allowed": False,
                    "execution_allowed": False,
                }
            ),
            created_by=request.actor_id,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_review(review)
        self._repository.save_request(
            activation_request.model_copy(
                update={
                    "status": _request_status(request.decision),
                    "reviewed_at": datetime.now(UTC),
                    "activation_allowed": False,
                    "execution_allowed": False,
                }
            )
        )
        self._emit("module_activation_review_recorded", saved, activation_request.owner_scope)
        return saved

    def list_reviews(
        self,
        scope: list[str],
        *,
        activation_request_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[ActivationReview]:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.review.read",
            scope,
            resource_type="module_activation_review",
        )
        return [
            item
            for item in self._repository.list_reviews(
                activation_request_id=activation_request_id,
                decision=decision,
                limit=limit,
            )
            if _review_in_scope(self._repository, item, scope)
        ]

    def _emit(self, event_type: str, review: ActivationReview, scope: list[str]) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="module_activation_review",
            node_id=review.activation_review_id,
            intensity=0.5,
            scope=scope,
            payload={"decision": review.decision, "activation_allowed": False},
        )


def _review_status(decision: str) -> ActivationReviewStatus:
    if decision == "approve_for_future_activation":
        return "approved"
    if decision == "reject":
        return "rejected"
    if decision == "block":
        return "blocked"
    if decision == "request_changes":
        return "changes_requested"
    return "recorded"


def _request_status(decision: str) -> str:
    if decision == "reject":
        return "rejected"
    if decision == "block":
        return "blocked"
    if decision in {"request_changes", "request_approval"}:
        return "review_required"
    return "reviewed"


def _review_in_scope(
    repository: ModuleActivationRepository,
    review: ActivationReview,
    scope: list[str],
) -> bool:
    request = repository.get_request(review.activation_request_id)
    return request is not None and _in_scope(request.owner_scope, scope)


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(requested_scope))


__all__ = ["ActivationReviewService"]
