"""Extension review service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.extensions import ExtensionReview, ExtensionReviewRequest
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository
from aion_brain.extensions.telemetry import emit_extension_telemetry


class ExtensionReviewService:
    """Record operator review decisions without installing extensions."""

    def __init__(
        self,
        repository: ExtensionRegistryRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def review(self, request: ExtensionReviewRequest, scope: list[str]) -> ExtensionReview:
        authorize_extension_action(
            self._policy_adapter,
            "extension.review",
            scope,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            resource_type="extension_review",
            resource_id=request.extension_package_id,
            risk_level="medium",
            approval_present=request.approval_present,
            context={"decision": request.decision},
        )
        package = self._repository.get_package(request.extension_package_id)
        if package is None:
            raise ValueError("extension_package_not_found")
        status = _review_status(request.decision)
        review = ExtensionReview(
            extension_review_id=f"extension-review-{uuid4().hex}",
            extension_package_id=request.extension_package_id,
            trace_id=package.trace_id,
            actor_id=request.actor_id or package.actor_id,
            workspace_id=request.workspace_id or package.workspace_id,
            status=status,
            decision=request.decision,
            reviewer_id=request.reviewer_id or request.actor_id,
            reason=request.reason,
            approval_request_id=cast(str | None, request.metadata.get("approval_request_id")),
            policy_decision_id=cast(str | None, request.metadata.get("policy_decision_id")),
            blocker_refs=list(request.metadata.get("blocker_refs") or []),
            metadata=request.metadata,
            created_by=request.actor_id,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_review(review)
        self._repository.save_package(
            package.model_copy(
                update={
                    "review_status": status,
                    "reviewed_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "status": _package_status_for_review(status, package.status),
                }
            )
        )
        emit_extension_telemetry(
            self._telemetry_service,
            event_type="extension_review_recorded",
            node_type="extension_review",
            node_id=saved.extension_review_id,
            scope=package.owner_scope,
            intensity=0.6,
            payload={
                "decision": saved.decision,
                "extension_package_id": saved.extension_package_id,
            },
        )
        return saved

    def list_reviews(
        self,
        scope: list[str],
        *,
        extension_package_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[ExtensionReview]:
        authorize_extension_action(
            self._policy_adapter,
            "extension.review",
            scope,
            resource_type="extension_review",
            risk_level="low",
        )
        return self._repository.list_reviews(
            extension_package_id=extension_package_id,
            decision=decision,
            limit=limit,
        )


def _review_status(decision: str) -> Any:
    return {
        "approve": "approved",
        "reject": "rejected",
        "block": "blocked",
        "request_changes": "pending",
        "request_approval": "pending",
    }[decision]


def _package_status_for_review(review_status: str, current: str) -> str:
    if review_status == "approved":
        return "accepted"
    if review_status == "rejected":
        return "rejected"
    if review_status == "blocked":
        return "rejected"
    return current if current != "proposed" else "review_required"


__all__ = ["ExtensionReviewService"]
