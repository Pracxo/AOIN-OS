"""Policy-gated Event Reaction Router."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.approvals import ApprovalCreateRequest
from aion_brain.contracts.autonomy import AutonomyDecisionRequest, AutonomyRiskLevel
from aion_brain.contracts.event_reactions import (
    EventDeadLetterRecord,
    EventDispatchRecord,
    EventDispatchRequest,
    EventDispatchStatus,
    EventReactionAction,
    EventReactionActionStatus,
    EventReactionRiskLevel,
    EventRouterStatus,
    EventSubscription,
    EventSubscriptionCreateRequest,
)
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessmentRequest
from aion_brain.event_reactions.actions import EventReactionActionRunner, action_type_for_target
from aion_brain.event_reactions.dead_letters import EventDeadLetterService
from aion_brain.event_reactions.matcher import EventTriggerMatcher
from aion_brain.event_reactions.repository import EventReactionRepository
from aion_brain.events.repository import EventRepository
from aion_brain.policy.base import PolicyAdapter


class EventReactionRouter:
    """Control plane that reacts to persisted AION events through subscriptions."""

    def __init__(
        self,
        *,
        repository: EventReactionRepository,
        event_repository: EventRepository,
        matcher: EventTriggerMatcher,
        action_runner: EventReactionActionRunner,
        dead_letter_service: EventDeadLetterService,
        policy_adapter: PolicyAdapter,
        settings: Settings,
        autonomy_governor: object | None = None,
        risk_engine: object | None = None,
        approval_service: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._event_repository = event_repository
        self._matcher = matcher
        self._action_runner = action_runner
        self._dead_letter_service = dead_letter_service
        self._policy_adapter = policy_adapter
        self._settings = settings
        self._autonomy_governor = autonomy_governor
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service

    def create_subscription(
        self,
        request: EventSubscriptionCreateRequest,
    ) -> EventSubscription:
        """Create a policy-gated subscription."""
        scope = request.owner_scope or ["workspace:main"]
        decision = self._authorize(
            "event.subscription.create",
            trace_id=None,
            actor_id=request.created_by,
            workspace_id=None,
            resource_type="event_subscription",
            resource_id=request.subscription_id,
            risk_level=request.risk_level,
            approval_present=True,
            scope=scope,
            context={"target_type": request.target_type, "reaction_mode": request.reaction_mode},
        )
        if not decision.allow:
            raise PermissionError(decision.reason)
        now = datetime.now(UTC)
        subscription = EventSubscription(
            subscription_id=request.subscription_id or f"event-subscription-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active" if request.activate else "disabled",
            owner_scope=scope,
            source_filters=request.source_filters,
            event_type_patterns=request.event_type_patterns,
            trigger_rules=request.trigger_rules,
            target_type=request.target_type,
            target_id=request.target_id,
            reaction_mode=request.reaction_mode,
            risk_level=request.risk_level,
            max_actions=request.max_actions,
            constraints=request.constraints,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None if request.activate else now,
        )
        saved = self._repository.save_subscription(subscription)
        self._emit(
            "event_subscription_created",
            "subscription",
            saved.subscription_id,
            None,
            {"target_type": saved.target_type, "status": saved.status},
        )
        return saved

    def get_subscription(self, subscription_id: str, scope: list[str]) -> EventSubscription | None:
        """Return a policy-authorized subscription."""
        self._authorize(
            "event.subscription.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            resource_type="event_subscription",
            resource_id=subscription_id,
            risk_level="low",
            approval_present=False,
            scope=scope,
            context={},
        )
        subscription = self._repository.get_subscription(subscription_id)
        if subscription is None or not _scope_matches(subscription.owner_scope, scope):
            return None
        return subscription

    def list_subscriptions(
        self,
        *,
        scope: list[str],
        status: str | None = None,
    ) -> list[EventSubscription]:
        """List policy-authorized subscriptions."""
        self._authorize(
            "event.subscription.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            resource_type="event_subscription",
            resource_id=None,
            risk_level="low",
            approval_present=False,
            scope=scope,
            context={"status": status},
        )
        return self._repository.list_subscriptions(scope=scope, status=status)

    def disable_subscription(
        self,
        subscription_id: str,
        *,
        actor_id: str | None,
        reason: str,
    ) -> EventSubscription:
        """Disable one subscription."""
        subscription = self._repository.get_subscription(subscription_id)
        if subscription is None:
            raise ValueError("event_subscription_not_found")
        decision = self._authorize(
            "event.subscription.disable",
            trace_id=None,
            actor_id=actor_id,
            workspace_id=None,
            resource_type="event_subscription",
            resource_id=subscription_id,
            risk_level="medium",
            approval_present=True,
            scope=subscription.owner_scope,
            context={"reason": reason},
        )
        if not decision.allow:
            raise PermissionError(decision.reason)
        saved = self._repository.save_subscription(
            subscription.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**subscription.metadata, "disable_reason": reason},
                }
            )
        )
        self._emit(
            "event_subscription_disabled",
            "subscription",
            saved.subscription_id,
            None,
            {"reason": reason},
        )
        return saved

    def dispatch(self, request: EventDispatchRequest) -> EventDispatchRecord:
        """Dispatch one event through matching subscriptions."""
        dispatch_id = request.dispatch_id or f"event-dispatch-{uuid4().hex}"
        if not self._settings.event_reaction_router_enabled:
            return self._persist_blocked_dispatch(
                request,
                dispatch_id,
                status="blocked_by_policy",
                reason="event_reaction_router_disabled",
            )

        event = request.event or (
            self._event_repository.get(request.event_id) if request.event_id else None
        )
        if event is None:
            return self._persist_blocked_dispatch(
                request,
                dispatch_id,
                status="failed",
                reason="event_not_found",
            )

        scope = request.owner_scope or event.security_scope or ["workspace:main"]
        policy = self._authorize(
            "event.dispatch",
            trace_id=request.trace_id or event.trace_id,
            actor_id=request.actor_id or event.actor_id,
            workspace_id=request.workspace_id or event.workspace_id,
            resource_type="event",
            resource_id=event.event_id,
            risk_level="low" if request.mode == "dry_run" else "medium",
            approval_present=request.approval_present,
            scope=scope,
            context={"mode": request.mode, "auto_dispatch": request.metadata.get("auto_dispatch")},
        )
        if not policy.allow and not policy.approval_required:
            return self._persist_event_dispatch(
                request,
                event,
                dispatch_id,
                "blocked_by_policy",
                [],
                [],
                {"reason": policy.reason, "owner_scope": scope},
            )

        autonomy = self._decide_autonomy(
            action_type="event.dispatch",
            event=event,
            request=request,
            risk_level="low" if request.mode == "dry_run" else "medium",
            resource_id=event.event_id,
            scope=scope,
        )
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return self._persist_event_dispatch(
                request,
                event,
                dispatch_id,
                "blocked_by_autonomy",
                [],
                [],
                {
                    "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                    "owner_scope": scope,
                },
            )

        subscriptions = self._load_candidate_subscriptions(request, scope)
        matched = self._matcher.match_subscriptions(event, subscriptions)
        max_actions = min(
            request.max_actions,
            self._settings.event_reaction_max_actions_default,
            100,
        )
        selected = matched[:max_actions]
        record = self._persist_event_dispatch(
            request,
            event,
            dispatch_id,
            "running",
            [subscription.subscription_id for subscription in selected],
            [],
            {
                "owner_scope": scope,
                "matched_count": len(matched),
                "truncated_count": max(0, len(matched) - len(selected)),
            },
        )
        actions = [
            self._handle_subscription(
                dispatch_id=dispatch_id,
                request=request,
                event=event,
                subscription=subscription,
            )
            for subscription in selected
        ]
        final_status = _final_status(request.mode, actions)
        completed = sum(action.status in {"completed", "dry_run", "skipped"} for action in actions)
        failed = sum(action.status == "failed" for action in actions)
        blocked = sum(
            action.status in {"blocked_by_policy", "blocked_by_autonomy", "waiting_for_approval"}
            for action in actions
        )
        final_record = record.model_copy(
            update={
                "status": final_status,
                "actions": actions,
                "action_count": len(actions),
                "completed_action_count": completed,
                "failed_action_count": failed,
                "blocked_action_count": blocked,
                "completed_at": datetime.now(UTC),
                "result": {
                    **record.result,
                    "policy_decision_id": policy.decision_id,
                    "action_statuses": [action.status for action in actions],
                },
            }
        )
        saved = self._repository.save_dispatch(final_record)
        self._emit(
            "event_dispatched",
            "dispatch",
            saved.dispatch_id,
            saved.trace_id,
            {"status": saved.status, "action_count": saved.action_count},
        )
        return saved

    def get_dispatch(self, dispatch_id: str, scope: list[str]) -> EventDispatchRecord | None:
        """Return a dispatch record."""
        self._authorize(
            "event.dispatch.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            resource_type="event_dispatch",
            resource_id=dispatch_id,
            risk_level="low",
            approval_present=False,
            scope=scope,
            context={},
        )
        record = self._repository.get_dispatch(dispatch_id)
        if record is None or not _scope_matches(_owner_scope_from_result(record.result), scope):
            return None
        return record

    def list_dispatches(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[EventDispatchRecord]:
        """List dispatch records."""
        self._authorize(
            "event.dispatch.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            resource_type="event_dispatch",
            resource_id=None,
            risk_level="low",
            approval_present=False,
            scope=scope,
            context={"status": status},
        )
        return self._repository.list_dispatches(scope=scope, status=status, limit=limit)

    def list_dead_letters(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[EventDeadLetterRecord]:
        """List dead letters through the router boundary."""
        return self._dead_letter_service.list_dead_letters(
            scope=scope,
            status=status,
            limit=limit,
        )

    def resolve_dead_letter(
        self,
        dead_letter_id: str,
        *,
        actor_id: str | None,
        reason: str,
    ) -> EventDeadLetterRecord:
        """Resolve a dead letter through the router boundary."""
        return self._dead_letter_service.mark_resolved(
            dead_letter_id,
            actor_id=actor_id,
            reason=reason,
        )

    def replay_dead_letter(
        self,
        dead_letter_id: str,
        *,
        approval_present: bool = False,
    ) -> EventDispatchRecord:
        """Replay a dead letter through the router boundary."""
        return self._dead_letter_service.replay(
            dead_letter_id,
            approval_present=approval_present,
        )

    def status(self, scope: list[str] | None = None) -> EventRouterStatus:
        """Return event router status."""
        query_scope = scope or ["workspace:main"]
        subscriptions = self._repository.list_subscriptions(scope=query_scope, status=None)
        active = [subscription for subscription in subscriptions if subscription.status == "active"]
        dead_letters = self._repository.list_dead_letters(
            scope=query_scope,
            status="open",
            limit=1000,
        )
        dispatches = self._repository.list_dispatches(scope=query_scope, limit=1)
        return EventRouterStatus(
            enabled=self._settings.event_reaction_router_enabled,
            auto_dispatch_enabled=self._settings.event_auto_dispatch_enabled,
            subscription_count=len(subscriptions),
            active_subscription_count=len(active),
            pending_dead_letter_count=len(dead_letters),
            latest_dispatch_id=dispatches[0].dispatch_id if dispatches else None,
            generated_at=datetime.now(UTC),
        )

    def _handle_subscription(
        self,
        *,
        dispatch_id: str,
        request: EventDispatchRequest,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> EventReactionAction:
        action = EventReactionAction(
            reaction_action_id=f"event-reaction-action-{uuid4().hex}",
            dispatch_id=dispatch_id,
            subscription_id=subscription.subscription_id,
            event_id=event.event_id,
            trace_id=request.trace_id or event.trace_id,
            target_type=subscription.target_type,
            target_id=subscription.target_id,
            action_type=action_type_for_target(subscription.target_type),
            mode=request.mode,
            status="running",
            input={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "owner_scope": subscription.owner_scope,
                "approval_present": request.approval_present,
            },
            output={},
            error={},
            created_at=datetime.now(UTC),
        )
        self._repository.save_action(action)
        self._emit(
            "event_reaction_started",
            "reaction",
            action.reaction_action_id,
            action.trace_id,
            {
                "subscription_id": subscription.subscription_id,
                "target_type": subscription.target_type,
            },
        )
        policy = self._authorize(
            "event.reaction.run",
            trace_id=action.trace_id,
            actor_id=request.actor_id or event.actor_id,
            workspace_id=request.workspace_id or event.workspace_id,
            resource_type=subscription.target_type,
            resource_id=subscription.target_id or subscription.subscription_id,
            risk_level=subscription.risk_level,
            approval_present=request.approval_present,
            scope=subscription.owner_scope,
            context={
                "target_type": subscription.target_type,
                "target_action_type": action.action_type,
                "mode": request.mode,
            },
        )
        action = action.model_copy(update={"policy_decision_id": policy.decision_id})
        if not policy.allow and not policy.approval_required:
            return self._complete_blocked_action(action, "blocked_by_policy", policy.reason)

        autonomy = self._decide_autonomy(
            action_type="event.reaction.run",
            event=event,
            request=request,
            risk_level=subscription.risk_level,
            resource_id=subscription.subscription_id,
            scope=subscription.owner_scope,
        )
        if autonomy is not None:
            action = action.model_copy(
                update={
                    "autonomy_decision_id": str(getattr(autonomy, "autonomy_decision_id", ""))
                    or None
                }
            )
            if not bool(getattr(autonomy, "allow", False)):
                reason = str(getattr(autonomy, "reason", "autonomy_denied"))
                if bool(getattr(autonomy, "approval_required", False)):
                    return self._create_waiting_action(action, subscription, event, reason)
                return self._complete_blocked_action(action, "blocked_by_autonomy", reason)

        risk = self._assess_risk(action, request, event, subscription)
        if risk is not None:
            action = action.model_copy(
                update={"risk_assessment_id": str(getattr(risk, "risk_assessment_id", "")) or None}
            )
            risk_decision = str(getattr(risk, "decision", "allow"))
            if risk_decision == "block":
                return self._complete_blocked_action(action, "blocked_by_policy", "risk_blocked")
            if risk_decision == "require_approval" and not request.approval_present:
                return self._create_waiting_action(action, subscription, event, "approval_required")

        if policy.approval_required and not request.approval_present:
            return self._create_waiting_action(action, subscription, event, policy.reason)

        if request.mode == "dry_run" or subscription.reaction_mode == "dry_run":
            completed = self._action_runner.dry_run(
                action=action,
                event=event,
                subscription=subscription,
            )
        else:
            completed = self._action_runner.run(
                action=action,
                event=event,
                subscription=subscription,
            )
        saved = self._repository.save_action(completed)
        if saved.status == "failed":
            self._dead_letter_service.create_dead_letter(
                dispatch_id=dispatch_id,
                action=saved,
                event=event,
                reason=str(saved.error.get("reason", "reaction_action_failed")),
                error=saved.error,
            )
            self._emit(
                "event_reaction_blocked",
                "reaction",
                saved.reaction_action_id,
                saved.trace_id,
                {"reason": "reaction_action_failed"},
            )
        else:
            self._emit(
                "event_reaction_completed",
                "reaction",
                saved.reaction_action_id,
                saved.trace_id,
                {"status": saved.status},
            )
        return saved

    def _complete_blocked_action(
        self,
        action: EventReactionAction,
        status: EventReactionActionStatus,
        reason: str,
    ) -> EventReactionAction:
        saved = self._repository.save_action(
            action.model_copy(
                update={
                    "status": status,
                    "error": {"reason": reason},
                    "completed_at": datetime.now(UTC),
                }
            )
        )
        self._emit(
            "event_reaction_blocked",
            "reaction",
            saved.reaction_action_id,
            saved.trace_id,
            {"status": status, "reason": reason},
        )
        return saved

    def _create_waiting_action(
        self,
        action: EventReactionAction,
        subscription: EventSubscription,
        event: AIONEvent,
        reason: str,
    ) -> EventReactionAction:
        approval_id = self._create_approval(action, subscription, event, reason)
        return self._complete_action(
            action,
            "waiting_for_approval",
            {"reason": reason, "approval_request_id": approval_id},
            approval_request_id=approval_id,
        )

    def _complete_action(
        self,
        action: EventReactionAction,
        status: EventReactionActionStatus,
        error: dict[str, Any],
        *,
        approval_request_id: str | None = None,
    ) -> EventReactionAction:
        return self._repository.save_action(
            action.model_copy(
                update={
                    "status": status,
                    "error": error,
                    "approval_request_id": approval_request_id,
                    "completed_at": datetime.now(UTC),
                }
            )
        )

    def _create_approval(
        self,
        action: EventReactionAction,
        subscription: EventSubscription,
        event: AIONEvent,
        reason: str,
    ) -> str | None:
        create_request = getattr(self._approval_service, "create_request", None)
        if not callable(create_request):
            return None
        approval = create_request(
            ApprovalCreateRequest(
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                action_type="event.reaction.run",
                resource_type=subscription.target_type,
                resource_id=subscription.target_id or subscription.subscription_id,
                title="Event reaction approval required",
                description="A generic event reaction requires approval before execution.",
                risk_assessment_id=action.risk_assessment_id,
                priority="high" if subscription.risk_level in {"high", "critical"} else "normal",
                approval_scope=subscription.owner_scope,
                payload={
                    "event_id": event.event_id,
                    "subscription_id": subscription.subscription_id,
                },
                constraints=[reason],
            )
        )
        return str(getattr(approval, "approval_request_id", "")) or None

    def _assess_risk(
        self,
        action: EventReactionAction,
        request: EventDispatchRequest,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> object | None:
        assess = getattr(self._risk_engine, "assess", None)
        if not callable(assess):
            return None
        result: object = assess(
            RiskAssessmentRequest(
                trace_id=event.trace_id,
                actor_id=request.actor_id or event.actor_id,
                workspace_id=request.workspace_id or event.workspace_id,
                action_type="event.reaction.run",
                resource_type=subscription.target_type,
                resource_id=subscription.target_id or subscription.subscription_id,
                requested_risk_level=subscription.risk_level,
                payload={"event_id": event.event_id, "target_type": subscription.target_type},
                context={
                    "security_scope": subscription.owner_scope,
                    "dry_run": request.mode == "dry_run",
                    "controlled_execution": request.mode == "controlled",
                    "approval_present": request.approval_present,
                    "target_action_type": action.action_type,
                },
                metadata={"subscription_id": subscription.subscription_id},
            )
        )
        return result

    def _decide_autonomy(
        self,
        *,
        action_type: str,
        event: AIONEvent,
        request: EventDispatchRequest,
        risk_level: EventReactionRiskLevel | str,
        resource_id: str,
        scope: list[str],
    ) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        result: object = decide(
            AutonomyDecisionRequest(
                trace_id=request.trace_id or event.trace_id,
                actor_id=request.actor_id or event.actor_id,
                workspace_id=request.workspace_id or event.workspace_id,
                requested_mode="dry_run" if request.mode == "dry_run" else "supervised_controlled",
                action_type=action_type,
                resource_type="event_reaction",
                resource_id=resource_id,
                risk_level=cast(AutonomyRiskLevel, risk_level),
                approval_present=request.approval_present,
                context={"security_scope": scope, "event_id": event.event_id},
                metadata={"source": "event_reaction_router"},
            )
        )
        return result

    def _load_candidate_subscriptions(
        self,
        request: EventDispatchRequest,
        scope: list[str],
    ) -> list[EventSubscription]:
        if request.subscription_ids:
            return [
                subscription
                for subscription in (
                    self._repository.get_subscription(subscription_id)
                    for subscription_id in request.subscription_ids
                )
                if subscription is not None
                and subscription.status == "active"
                and _scope_matches(subscription.owner_scope, scope)
            ]
        return self._repository.list_subscriptions(scope=scope, status="active")

    def _persist_blocked_dispatch(
        self,
        request: EventDispatchRequest,
        dispatch_id: str,
        *,
        status: EventDispatchStatus,
        reason: str,
    ) -> EventDispatchRecord:
        event_id = request.event.event_id if request.event is not None else request.event_id
        return self._repository.save_dispatch(
            EventDispatchRecord(
                dispatch_id=dispatch_id,
                event_id=event_id or "unknown",
                trace_id=request.trace_id or (request.event.trace_id if request.event else None),
                actor_id=request.actor_id or (request.event.actor_id if request.event else None),
                workspace_id=request.workspace_id
                or (request.event.workspace_id if request.event else None),
                status=status,
                mode=request.mode,
                matched_subscription_ids=[],
                actions=[],
                action_count=0,
                completed_action_count=0,
                failed_action_count=1 if status == "failed" else 0,
                blocked_action_count=1 if status != "failed" else 0,
                result={"reason": reason, "owner_scope": request.owner_scope},
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
        )

    def _persist_event_dispatch(
        self,
        request: EventDispatchRequest,
        event: AIONEvent,
        dispatch_id: str,
        status: EventDispatchStatus,
        matched_subscription_ids: list[str],
        actions: list[EventReactionAction],
        result: dict[str, Any],
    ) -> EventDispatchRecord:
        return self._repository.save_dispatch(
            EventDispatchRecord(
                dispatch_id=dispatch_id,
                event_id=event.event_id,
                trace_id=request.trace_id or event.trace_id,
                actor_id=request.actor_id or event.actor_id,
                workspace_id=request.workspace_id or event.workspace_id,
                status=status,
                mode=request.mode,
                matched_subscription_ids=matched_subscription_ids,
                actions=actions,
                action_count=len(actions),
                completed_action_count=0,
                failed_action_count=0,
                blocked_action_count=0,
                result=result,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC) if status != "running" else None,
            )
        )

    def _authorize(
        self,
        action_type: str,
        *,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        approval_present: bool,
        scope: list[str],
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        trace_id: str | None,
        payload: dict[str, object],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        from aion_brain.contracts.telemetry import (
            VisualNodeType,
            VisualTelemetryEvent,
            VisualTelemetryEventType,
        )

        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-event-router-{uuid4().hex}",
                    trace_id=trace_id or f"event-router-{uuid4().hex}",
                    event_type=cast(VisualTelemetryEventType, event_type),
                    node_type=cast(VisualNodeType, node_type),
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=0.75,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return not requested_scope or bool(set(owner_scope).intersection(requested_scope))


def _owner_scope_from_result(result: dict[str, Any]) -> list[str]:
    owner_scope = result.get("owner_scope")
    if isinstance(owner_scope, list):
        return [str(item) for item in owner_scope]
    return ["workspace:main"]


def _final_status(
    mode: str,
    actions: list[EventReactionAction],
) -> EventDispatchStatus:
    if not actions:
        return "completed"
    statuses = {action.status for action in actions}
    if mode == "dry_run" and statuses <= {"dry_run", "skipped", "completed"}:
        return "dry_run"
    if statuses <= {"completed", "skipped", "dry_run"}:
        return "completed"
    if statuses <= {"blocked_by_autonomy"}:
        return "blocked_by_autonomy"
    if statuses <= {"blocked_by_policy", "waiting_for_approval"}:
        return "blocked_by_policy"
    if statuses <= {"failed"}:
        return "failed"
    return "partially_completed"
