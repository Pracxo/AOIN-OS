"""Recovery review service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.root_cause import RecoveryReview, RecoveryReviewRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry

_GENERIC_RECOMMENDATIONS = [
    "review_source_alerts",
    "inspect_run_supervision",
    "run_grounding_verification",
    "run_audit_verification",
    "review_policy_decision",
    "request_approval",
    "create_compensation_plan",
    "create_action_proposal",
    "run_operator_readiness",
]


class RecoveryReviewService:
    """Build local recovery reviews without executing remediation."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        root_cause_service: object | None = None,
        action_proposal_service: object | None = None,
        compensation_planner: object | None = None,
        notification_router: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._root_cause_service = root_cause_service
        self._action_proposal_service = action_proposal_service
        self._compensation_planner = compensation_planner
        self._notification_router = notification_router
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RecoveryReviewService:
        return RecoveryReviewService(
            self._repository,
            self._policy_adapter,
            root_cause_service=self._root_cause_service,
            action_proposal_service=self._action_proposal_service,
            compensation_planner=self._compensation_planner,
            notification_router=self._notification_router,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_review(self, request: RecoveryReviewRequest) -> RecoveryReview:
        authorize(
            self._policy_adapter,
            action_type="incident.recovery_review.create",
            resource_type="recovery_review",
            resource_id=request.recovery_review_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.created_by or self._actor_context.actor_id,
            risk_level="medium",
            context={"remediation_execution": False},
        )
        incident = _get_incident(self._repository, request.incident_id)
        if incident is None:
            raise ValueError("incident_not_found")
        candidates = _list_candidates(self._repository, request.incident_id)
        created_records: list[dict[str, object]] = []
        action_refs: list[str] = []
        compensation_refs: list[str] = []
        notification_refs: list[str] = []
        if request.create_action_proposals:
            ref = _create_action_proposal(self._action_proposal_service, request, incident)
            if ref:
                action_refs.append(ref)
                created_records.append({"record_type": "action_proposal", "record_id": ref})
        if request.create_compensation_plans:
            ref = _create_compensation_plan(self._compensation_planner, request, incident)
            if ref:
                compensation_refs.append(ref)
                created_records.append({"record_type": "compensation_plan", "record_id": ref})
        if request.create_notifications:
            ref = _create_notification(self._notification_router, request, incident)
            if ref:
                notification_refs.append(ref)
                created_records.append({"record_type": "notification", "record_id": ref})
        now = datetime.now(UTC)
        review = RecoveryReview(
            recovery_review_id=request.recovery_review_id or f"recovery-review-{uuid4().hex}",
            incident_id=request.incident_id,
            trace_id=request.trace_id or getattr(incident, "trace_id", None),
            status="completed",
            review_type=request.review_type,
            title="Incident recovery review",
            summary="Generic recovery options were reviewed without executing remediation.",
            owner_scope=request.owner_scope,
            findings=[
                {
                    "type": "root_cause_candidate",
                    "candidate_id": getattr(candidate, "root_cause_candidate_id", None),
                    "candidate_not_truth": True,
                }
                for candidate in candidates
            ],
            recommendations=[
                {"recommendation": item, "executes": False} for item in _GENERIC_RECOMMENDATIONS
            ],
            action_proposal_refs=action_refs,
            compensation_plan_refs=compensation_refs,
            notification_refs=notification_refs,
            outcome_refs=getattr(incident, "outcome_refs", []),
            created_records=created_records,
            metadata={
                **request.metadata,
                "remediation_executed": False,
                "source_records_mutated": False,
            },
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        stored = _save_review(self._repository, review)
        emit_telemetry(
            self._telemetry_service,
            event_type="recovery_review_created",
            node_type="recovery_review",
            node_id=stored.recovery_review_id,
            intensity=0.6,
            trace_id=stored.trace_id,
            payload={"review_type": stored.review_type, "remediation_executed": False},
        )
        return stored

    def get_review(self, recovery_review_id: str, scope: list[str]) -> RecoveryReview | None:
        authorize(
            self._policy_adapter,
            action_type="incident.recovery_review.read",
            resource_type="recovery_review",
            resource_id=recovery_review_id,
            scope=scope,
            risk_level="low",
        )
        get = getattr(self._repository, "get_recovery_review", None)
        review = get(recovery_review_id) if callable(get) else None
        if not isinstance(review, RecoveryReview):
            return None
        return review if bool(set(review.owner_scope).intersection(scope)) else None

    def list_reviews(
        self,
        scope: list[str],
        incident_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[RecoveryReview]:
        authorize(
            self._policy_adapter,
            action_type="incident.recovery_review.read",
            resource_type="recovery_review",
            resource_id=incident_id,
            scope=scope,
            risk_level="low",
        )
        list_reviews = getattr(self._repository, "list_recovery_reviews", None)
        if not callable(list_reviews):
            return []
        return list(
            list_reviews(scope=scope, incident_id=incident_id, status=status, limit=limit) or []
        )


def _get_incident(repository: object, incident_id: str) -> object | None:
    get = getattr(repository, "get_incident", None)
    return get(incident_id) if callable(get) else None


def _list_candidates(repository: object, incident_id: str) -> list[object]:
    list_candidates = getattr(repository, "list_root_causes", None)
    if not callable(list_candidates):
        return []
    return list(list_candidates(incident_id=incident_id, limit=100) or [])


def _save_review(repository: object, review: RecoveryReview) -> RecoveryReview:
    save = getattr(repository, "save_recovery_review", None)
    stored = save(review) if callable(save) else review
    return stored if isinstance(stored, RecoveryReview) else review


def _create_action_proposal(
    service: object | None, request: RecoveryReviewRequest, incident: object
) -> str | None:
    create = getattr(service, "create_proposal", None)
    if not callable(create):
        return None
    try:
        from aion_brain.contracts.action_proposals import ActionProposalCreateRequest

        proposal = create(
            ActionProposalCreateRequest(
                trace_id=request.trace_id or getattr(incident, "trace_id", None),
                source_type="operator",
                source_id=request.incident_id,
                proposal_type="generic",
                title="Review incident recovery option",
                description=(
                    "Action proposal created from a recovery review; no execution occurred."
                ),
                action_type="generic",
                target_type="incident",
                target_id=request.incident_id,
                owner_scope=request.owner_scope,
                proposed_payload={"recommended_action": "review_incident_recovery"},
                required_permissions=[],
                required_approvals=[],
                risk_level="medium",
                created_by=request.created_by,
            )
        )
        return str(getattr(proposal, "action_proposal_id", ""))
    except Exception:
        return None


def _create_compensation_plan(
    planner: object | None, request: RecoveryReviewRequest, incident: object
) -> str | None:
    create = getattr(planner, "create_plan", None)
    if not callable(create):
        return None
    try:
        plan = create(
            {
                "incident_id": request.incident_id,
                "trace_id": request.trace_id or getattr(incident, "trace_id", None),
                "owner_scope": request.owner_scope,
                "execute": False,
            }
        )
        return str(getattr(plan, "compensation_plan_id", None) or plan.get("compensation_plan_id"))
    except Exception:
        return None


def _create_notification(
    router: object | None, request: RecoveryReviewRequest, incident: object
) -> str | None:
    publish = getattr(router, "publish", None)
    if not callable(publish):
        return None
    try:
        notification = publish(
            {
                "source_type": "incident",
                "source_id": request.incident_id,
                "title": "Incident recovery review created",
                "message": "A local recovery review was created.",
                "owner_scope": request.owner_scope,
                "trace_id": request.trace_id or getattr(incident, "trace_id", None),
            }
        )
        return str(
            getattr(notification, "notification_id", None) or notification.get("notification_id")
        )
    except Exception:
        return None


__all__ = ["RecoveryReviewService"]
