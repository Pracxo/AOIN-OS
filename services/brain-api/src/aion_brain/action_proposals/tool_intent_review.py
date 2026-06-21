"""Tool intent review service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import ToolIntentReview, ToolIntentReviewRequest
from aion_brain.contracts.model_outputs import ToolIntentCandidate
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ToolIntentReviewService:
    """Review captured model tool intents without executing them."""

    def __init__(
        self,
        repository: object,
        tool_intent_repository: object,
        policy_adapter: object | None,
        *,
        action_proposal_service: object | None = None,
        blocker_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._tool_intent_repository = tool_intent_repository
        self._policy_adapter = policy_adapter
        self._action_proposal_service = action_proposal_service
        self._blocker_service = blocker_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ToolIntentReviewService:
        return ToolIntentReviewService(
            self._repository,
            self._tool_intent_repository,
            self._policy_adapter,
            action_proposal_service=self._action_proposal_service,
            blocker_service=self._blocker_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def review(self, request: ToolIntentReviewRequest) -> ToolIntentReview:
        """Review a tool intent. This never dispatches the tool."""

        if self._settings is not None and not bool(
            getattr(self._settings, "tool_intent_review_enabled", True)
        ):
            raise RuntimeError("tool_intent_review_disabled")
        authorize(
            self._policy_adapter,
            action_type="action_proposal.tool_intent.review",
            resource_type="tool_intent",
            resource_id=request.tool_intent_id,
            scope=request.owner_scope,
            trace_id=self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            approval_present=request.approval_present,
        )
        intent = _require_tool_intent(self._tool_intent_repository, request.tool_intent_id)
        blocker_refs: list[str] = []
        action_proposal_id = None
        decision = request.decision
        reason = "tool_intent_reviewed"
        execution_enabled = bool(getattr(self._settings, "tool_intent_execution_enabled", False))
        if not execution_enabled:
            blocker_refs.append(self._create_blocker(intent, request, "tool_execution_disabled"))
            decision = "block"
            reason = "tool_intent_execution_disabled"
        elif request.decision == "create_proposal":
            build = getattr(self._action_proposal_service, "build_from_tool_intent", None)
            if callable(build):
                proposal = build(
                    request.tool_intent_id,
                    request.owner_scope,
                    request.created_by or request.actor_id,
                )
                action_proposal_id = getattr(proposal, "action_proposal_id", None)
                reason = "action_proposal_created"
        elif request.decision in {"reject", "block", "needs_clarification", "unsupported"}:
            reason = request.decision
        review = ToolIntentReview(
            tool_intent_review_id=f"tool-intent-review-{uuid4().hex}",
            tool_intent_id=request.tool_intent_id,
            trace_id=intent.trace_id,
            status="completed",
            decision=decision,
            action_proposal_id=action_proposal_id,
            blocker_refs=blocker_refs,
            reason=reason,
            metadata={**request.metadata, "no_execution": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_tool_intent_review", None)
        stored = save(review) if callable(save) else review
        stored = stored if isinstance(stored, ToolIntentReview) else review
        self._record_audit("tool_intent_reviewed", stored.tool_intent_review_id)
        if action_proposal_id is not None:
            self._record_provenance(
                request.tool_intent_id, action_proposal_id, "converted_to_proposal"
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="tool_intent_reviewed",
            node_type="tool_intent_review",
            node_id=stored.tool_intent_review_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            payload={"decision": stored.decision, "blocker_refs": stored.blocker_refs},
        )
        return stored

    def list_reviews(
        self,
        tool_intent_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ToolIntentReview]:
        list_reviews = getattr(self._repository, "list_tool_intent_reviews", None)
        if not callable(list_reviews):
            return []
        result = list_reviews(tool_intent_id=tool_intent_id, status=status, limit=limit)
        return [item for item in result if isinstance(item, ToolIntentReview)]

    def _create_blocker(
        self,
        intent: ToolIntentCandidate,
        request: ToolIntentReviewRequest,
        reason: str,
    ) -> str:
        create = getattr(self._blocker_service, "create_blocker", None)
        if not callable(create):
            return reason
        blocker = create(
            blocker_type="tool_execution_disabled",
            severity="high",
            reason=reason,
            trace_id=intent.trace_id,
            source_type="tool_intent",
            source_id=request.tool_intent_id,
        )
        return str(getattr(blocker, "action_blocker_id", reason))

    def _record_audit(self, event_type: str, review_id: str) -> None:
        record = getattr(self._audit_sink, "record_event", None)
        if callable(record):
            try:
                record({"event_type": event_type, "tool_intent_review_id": review_id})
            except Exception:
                return

    def _record_provenance(self, source_id: str, target_id: str, relation_type: str) -> None:
        link = getattr(self._provenance_service, "record_link", None)
        if callable(link):
            try:
                link(source_id, target_id, relation_type)
            except Exception:
                return


def _require_tool_intent(repository: object, tool_intent_id: str) -> ToolIntentCandidate:
    get = getattr(repository, "get_tool_intent", None)
    intent = get(tool_intent_id) if callable(get) else None
    if not isinstance(intent, ToolIntentCandidate):
        raise ValueError("tool_intent_not_found")
    return intent


__all__ = ["ToolIntentReviewService"]
