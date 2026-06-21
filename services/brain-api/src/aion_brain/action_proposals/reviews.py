"""Action proposal review service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import (
    ActionProposal,
    ActionProposalReview,
    ActionProposalReviewRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ActionReviewService:
    """Review proposals through policy, risk, approval, and autonomy gates."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        blocker_service: object | None = None,
        risk_engine: object | None = None,
        autonomy_governor: object | None = None,
        approval_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._blocker_service = blocker_service
        self._risk_engine = risk_engine
        self._autonomy_governor = autonomy_governor
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ActionReviewService:
        return ActionReviewService(
            self._repository,
            self._policy_adapter,
            blocker_service=self._blocker_service,
            risk_engine=self._risk_engine,
            autonomy_governor=self._autonomy_governor,
            approval_service=self._approval_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            actor_context=actor_context,
        )

    def review(self, request: ActionProposalReviewRequest) -> ActionProposalReview:
        """Review a proposal. This does not hand off or execute anything."""

        proposal = _require_proposal(self._repository, request.action_proposal_id)
        authorize(
            self._policy_adapter,
            action_type="action_proposal.review",
            resource_type="action_proposal",
            resource_id=proposal.action_proposal_id,
            scope=proposal.owner_scope,
            trace_id=proposal.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=proposal.risk_level,
            approval_present=request.approval_present,
            context={"requested_decision": request.decision},
        )
        blocker_refs: list[str] = []
        decision = request.decision
        approval_request_id = None
        risk_blocker = self._risk_blocker(proposal)
        if risk_blocker is not None:
            blocker_refs.append(risk_blocker)
            decision = "block"
        autonomy_blocker = self._autonomy_blocker(proposal)
        if autonomy_blocker is not None:
            blocker_refs.append(autonomy_blocker)
            decision = "block"
        if (
            proposal.risk_level in {"high", "critical"}
            and not request.approval_present
            and decision == "approve_for_handoff"
        ):
            approval_request_id = self._approval_request_id(proposal)
            blocker_refs.append(
                self._create_blocker(
                    proposal,
                    blocker_type="approval_required",
                    severity=proposal.risk_level,
                    reason="approval_required_before_handoff",
                )
            )
            decision = "request_approval"
        status_update = _status_for_decision(decision)
        updated = proposal.model_copy(
            update={
                "status": status_update,
                "reviewed_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "blocker_refs": sorted(set([*proposal.blocker_refs, *blocker_refs])),
            }
        )
        _save_proposal(self._repository, updated)
        review = ActionProposalReview(
            action_review_id=f"action-review-{uuid4().hex}",
            action_proposal_id=proposal.action_proposal_id,
            trace_id=proposal.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status="completed",
            decision=decision,
            reviewer_id=request.reviewer_id,
            reason=request.reason,
            policy_decision_id=None,
            risk_assessment_id=None,
            autonomy_decision_id=None,
            approval_request_id=approval_request_id,
            blocker_refs=blocker_refs,
            metadata={**request.metadata, "no_handoff": True},
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_review", None)
        stored = save(review) if callable(save) else review
        stored = stored if isinstance(stored, ActionProposalReview) else review
        self._record_audit("action_proposal_reviewed", stored.action_review_id)
        self._record_provenance(proposal.action_proposal_id, stored.action_review_id, "reviewed_as")
        emit_telemetry(
            self._telemetry_service,
            event_type="action_proposal_reviewed",
            node_type="action_review",
            node_id=stored.action_review_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            payload={"decision": stored.decision, "blocker_refs": stored.blocker_refs},
        )
        return stored

    def list_reviews(
        self,
        action_proposal_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[ActionProposalReview]:
        """List proposal reviews."""

        list_reviews = getattr(self._repository, "list_reviews", None)
        if not callable(list_reviews):
            return []
        result = list_reviews(action_proposal_id=action_proposal_id, decision=decision, limit=limit)
        return [item for item in result if isinstance(item, ActionProposalReview)]

    def _risk_blocker(self, proposal: ActionProposal) -> str | None:
        result = _call_gate(self._risk_engine, "assess", proposal)
        if _gate_denied(result):
            return self._create_blocker(
                proposal,
                blocker_type="risk_too_high",
                severity=proposal.risk_level,
                reason="risk_gate_denied",
            )
        return None

    def _autonomy_blocker(self, proposal: ActionProposal) -> str | None:
        result = _call_gate(self._autonomy_governor, "decide", proposal)
        if _gate_denied(result):
            return self._create_blocker(
                proposal,
                blocker_type="autonomy_denied",
                severity="high",
                reason="autonomy_gate_denied",
            )
        return None

    def _approval_request_id(self, proposal: ActionProposal) -> str:
        create = getattr(self._approval_service, "create_request", None)
        if callable(create):
            try:
                result = create({"action_proposal_id": proposal.action_proposal_id})
                request_id = getattr(result, "approval_request_id", None)
                if isinstance(request_id, str):
                    return request_id
            except Exception:
                return "approval_required"
        return "approval_required"

    def _create_blocker(
        self,
        proposal: ActionProposal,
        *,
        blocker_type: str,
        severity: str,
        reason: str,
    ) -> str:
        create = getattr(self._blocker_service, "create_blocker", None)
        if not callable(create):
            return reason
        blocker = create(
            action_proposal_id=proposal.action_proposal_id,
            trace_id=proposal.trace_id,
            blocker_type=blocker_type,
            severity=severity,
            reason=reason,
            source_type="action_proposal",
            source_id=proposal.action_proposal_id,
        )
        return str(getattr(blocker, "action_blocker_id", reason))

    def _record_audit(self, event_type: str, action_review_id: str) -> None:
        record = getattr(self._audit_sink, "record_event", None)
        if callable(record):
            try:
                record({"event_type": event_type, "action_review_id": action_review_id})
            except Exception:
                return

    def _record_provenance(self, source_id: str, target_id: str, relation_type: str) -> None:
        link = getattr(self._provenance_service, "record_link", None)
        if callable(link):
            try:
                link(source_id, target_id, relation_type)
            except Exception:
                return


def _require_proposal(repository: object, action_proposal_id: str) -> ActionProposal:
    get = getattr(repository, "get_proposal", None)
    proposal = get(action_proposal_id) if callable(get) else None
    if not isinstance(proposal, ActionProposal):
        raise ValueError("action_proposal_not_found")
    return proposal


def _save_proposal(repository: object, proposal: ActionProposal) -> ActionProposal:
    save = getattr(repository, "save_proposal", None)
    stored = save(proposal) if callable(save) else proposal
    return stored if isinstance(stored, ActionProposal) else proposal


def _status_for_decision(decision: str) -> str:
    if decision == "approve_for_handoff":
        return "approved_for_handoff"
    if decision in {"reject", "request_clarification"}:
        return "rejected"
    if decision in {"block", "request_approval"}:
        return "blocked"
    return "under_review"


def _call_gate(service: object | None, method: str, proposal: ActionProposal) -> object | None:
    call = getattr(service, method, None)
    if not callable(call):
        return None
    try:
        result: object = call(proposal)
        return result
    except Exception:
        return {"allow": False}


def _gate_denied(result: object | None) -> bool:
    if result is None:
        return False
    if isinstance(result, bool):
        return not result
    if isinstance(result, dict) and "allow" in result:
        return result.get("allow") is False
    allow = getattr(result, "allow", None)
    if isinstance(allow, bool):
        return not allow
    status = getattr(result, "status", None)
    return status in {"denied", "blocked", "failed"}


__all__ = ["ActionReviewService"]
