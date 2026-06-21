"""Lifecycle review service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.lifecycle import (
    LifecycleCandidateType,
    LifecycleReviewDecision,
    LifecycleReviewRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class LifecycleReviewService:
    """Record lifecycle reviews without executing lifecycle actions."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        archive_planner: object | None = None,
        redaction_planner: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._archive_planner = archive_planner
        self._redaction_planner = redaction_planner
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> LifecycleReviewService:
        return LifecycleReviewService(
            self._repository,
            self._policy_adapter,
            archive_planner=self._archive_planner,
            redaction_planner=self._redaction_planner,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def review_candidate(
        self,
        candidate_type: str,
        candidate_id: str,
        decision: str,
        actor_id: str | None,
        reason: str,
        approval_present: bool = False,
    ) -> LifecycleReviewRecord:
        candidate = _load_candidate(self._repository, candidate_type, candidate_id)
        scope = list(getattr(candidate, "owner_scope", []) or ["workspace:main"])
        authorize(
            self._policy_adapter,
            action_type="lifecycle.review.create",
            resource_type="lifecycle_review",
            resource_id=candidate_id,
            scope=scope,
            trace_id=getattr(candidate, "trace_id", self._actor_context.trace_id),
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            approval_present=approval_present,
            context={"review_only": True},
        )
        action_proposal_id = None
        if decision == "approve_for_action_proposal":
            action_proposal_id = _convert_candidate(
                candidate_type,
                candidate_id,
                actor_id,
                approval_present,
                reason,
                self._archive_planner,
                self._redaction_planner,
                self._actor_context,
            )
        review = LifecycleReviewRecord(
            lifecycle_review_id=f"lifecycle-review-{uuid4().hex}",
            trace_id=getattr(candidate, "trace_id", self._actor_context.trace_id),
            resource_uri=getattr(candidate, "resource_uri", None),
            candidate_type=cast(LifecycleCandidateType, candidate_type),
            candidate_id=candidate_id,
            status="recorded",
            decision=cast(LifecycleReviewDecision, decision),
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            reason=reason,
            action_proposal_id=action_proposal_id,
            owner_scope=scope,
            metadata={"executed": False},
            created_by=actor_id or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_review(self._repository, review)
        emit_telemetry(
            self._telemetry_service,
            event_type="lifecycle_review_recorded",
            node_type="lifecycle_review",
            node_id=stored.lifecycle_review_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"decision": stored.decision, "candidate_type": stored.candidate_type},
        )
        return stored

    def list_reviews(
        self,
        scope: list[str],
        candidate_type: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[LifecycleReviewRecord]:
        authorize(
            self._policy_adapter,
            action_type="lifecycle.review.read",
            resource_type="lifecycle_review",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_reviews", None)
        return (
            list_items(scope, candidate_type=candidate_type, decision=decision, limit=limit)
            if callable(list_items)
            else []
        )


def _load_candidate(repository: object, candidate_type: str, candidate_id: str) -> object:
    method_name = {
        "archive": "get_archive_candidate",
        "redaction": "get_redaction_candidate",
        "purge_preview": "get_purge_preview",
    }.get(candidate_type)
    get = getattr(repository, method_name or "", None)
    item = get(candidate_id) if callable(get) else None
    if item is None:
        raise ValueError("lifecycle_candidate_not_found")
    return item


def _convert_candidate(
    candidate_type: str,
    candidate_id: str,
    actor_id: str | None,
    approval_present: bool,
    reason: str,
    archive_planner: object | None,
    redaction_planner: object | None,
    actor_context: ActorContext,
) -> str | None:
    planner = archive_planner if candidate_type == "archive" else redaction_planner
    with_context = getattr(planner, "with_actor_context", None)
    if callable(with_context):
        planner = with_context(actor_context)
    convert = getattr(planner, "convert_to_action_proposal", None)
    if not callable(convert):
        return None
    converted = convert(candidate_id, actor_id, approval_present, reason)
    return getattr(converted, "action_proposal_id", None)


def _save_review(repository: object, review: LifecycleReviewRecord) -> LifecycleReviewRecord:
    save = getattr(repository, "save_review", None)
    stored = save(review) if callable(save) else review
    return stored if isinstance(stored, LifecycleReviewRecord) else review


__all__ = ["LifecycleReviewService"]
