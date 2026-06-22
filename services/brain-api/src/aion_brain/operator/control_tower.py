"""Operator Control Tower top-level service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.operator import (
    OperatorActionItem,
    OperatorOverallStatus,
    OperatorOverview,
    OperatorOverviewRequest,
    OperatorQueueSummary,
    OperatorReadinessReport,
    OperatorStatusCard,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.operator.action_center import ActionCenterService, _emit
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.readiness import ReadinessAggregator
from aion_brain.operator.runbooks import RunbookRegistry
from aion_brain.operator.status_cards import StatusCardBuilder


class OperatorControlTowerService:
    """Read-mostly backend aggregation service for local operators."""

    def __init__(
        self,
        *,
        status_cards: StatusCardBuilder,
        queues: QueueSummaryBuilder,
        action_center: ActionCenterService,
        readiness: ReadinessAggregator,
        runbooks: RunbookRegistry,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._status_cards = status_cards
        self._queues = queues
        self._action_center = action_center
        self._readiness = readiness
        self._runbooks = runbooks
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def overview(
        self,
        request: OperatorOverviewRequest,
        *,
        actor_context: ActorContext | None = None,
    ) -> OperatorOverview:
        """Return a generic read-only local operator overview."""
        self._authorize(
            "operator.overview.read",
            request.owner_scope,
            "operator",
            None,
            actor_context=actor_context,
        )
        cards = (
            self.status_cards(request.owner_scope, actor_context=actor_context)
            if request.include_cards
            else []
        )
        queues = (
            self.queues(request.owner_scope, actor_context=actor_context)
            if request.include_queues
            else []
        )
        actions = (
            self.actions(request.owner_scope, actor_context=actor_context)
            if request.include_actions
            else []
        )
        readiness = (
            self.readiness(request.owner_scope, actor_context=actor_context).model_dump(
                mode="json"
            )
            if request.include_readiness
            else {}
        )
        runbooks = (
            [item.model_dump(mode="json") for item in self._runbooks.list_runbooks()]
            if request.include_runbooks
            else []
        )
        overview = OperatorOverview(
            overview_id=f"overview-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            overall_status=_overall_status(cards, queues, actions),
            cards=cards,
            queues=queues,
            actions=actions,
            readiness=readiness,
            runbooks=runbooks,
            generated_at=datetime.now(UTC),
        )
        _emit(
            self._telemetry_service,
            "operator_overview_generated",
            "operator",
            overview.overview_id,
            0.5,
            {"overall_status": overview.overall_status},
            request.trace_id,
        )
        return overview

    def readiness(
        self,
        scope: list[str],
        *,
        actor_context: ActorContext | None = None,
    ) -> OperatorReadinessReport:
        """Return operator readiness."""
        self._authorize(
            "operator.readiness.read",
            scope,
            "operator_readiness",
            None,
            actor_context=actor_context,
        )
        return self._readiness.build_report(scope, actor_context=actor_context)

    def status_cards(
        self,
        scope: list[str],
        *,
        actor_context: ActorContext | None = None,
    ) -> list[OperatorStatusCard]:
        """Return status cards."""
        self._authorize(
            "operator.cards.read",
            scope,
            "operator_status_cards",
            None,
            actor_context=actor_context,
        )
        return self._status_cards.build_cards(scope)

    def queues(
        self,
        scope: list[str],
        *,
        actor_context: ActorContext | None = None,
    ) -> list[OperatorQueueSummary]:
        """Return queue summaries."""
        self._authorize(
            "operator.queues.read",
            scope,
            "operator_queues",
            None,
            actor_context=actor_context,
        )
        queues = self._queues.build_queues(scope)
        for queue in queues:
            _emit(
                self._telemetry_service,
                "operator_queue_summary_generated",
                "queue",
                queue.queue_id,
                0.4,
                {"queue_type": queue.queue_type, "status": queue.status},
                None,
            )
        return queues

    def actions(
        self,
        scope: list[str],
        limit: int = 100,
        *,
        actor_context: ActorContext | None = None,
    ) -> list[OperatorActionItem]:
        """Return action center items."""
        self._authorize(
            "operator.actions.read",
            scope,
            "operator_action_items",
            None,
            actor_context=actor_context,
        )
        return self._action_center.build_action_items(
            scope,
            limit,
            actor_context=actor_context,
        )

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        resource_type: str,
        resource_id: str | None,
        *,
        actor_context: ActorContext | None = None,
    ) -> None:
        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return
        context: dict[str, Any] = {"source": "operator_control_tower"}
        if actor_context is not None:
            context["actor_context"] = actor_context.model_dump(mode="json")
        decision = authorize(
            PolicyRequest(
                request_id=f"operator-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_context.actor_id if actor_context is not None else None,
                workspace_id=actor_context.workspace_id if actor_context is not None else None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)


def _overall_status(
    cards: list[OperatorStatusCard],
    queues: list[OperatorQueueSummary],
    actions: Sequence[object],
) -> OperatorOverallStatus:
    if any(getattr(item, "severity", None) == "critical" for item in actions):
        return "blocked"
    statuses = [card.status for card in cards] + [queue.status for queue in queues]
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "degraded" for status in statuses):
        return "degraded"
    if any(status in {"warning", "unknown"} for status in statuses):
        return "warning"
    return "ready"
