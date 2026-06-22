"""Goal Manager service."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.goals import GoalCreateRequest, GoalRecord, GoalTransitionRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.tasks import TaskLifecycleEvent
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.goals.repository import GoalRepository
from aion_brain.lifecycle.state_machine import require_valid_goal_transition
from aion_brain.policy.base import PolicyAdapter
from aion_brain.tasks.publisher import TaskLifecyclePublisher


class GoalService:
    """Policy-gated goal lifecycle service."""

    def __init__(
        self,
        *,
        repository: GoalRepository | object,
        policy_adapter: PolicyAdapter,
        publisher: TaskLifecyclePublisher | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._publisher = publisher
        self._telemetry_service = telemetry_service

    def create_goal(self, request: GoalCreateRequest) -> GoalRecord:
        """Create a proposed goal."""
        decision = self._authorize(
            action_type="goal.create",
            resource_id=request.goal_id,
            risk_level=request.risk_level,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        goal = GoalRecord(
            goal_id=request.goal_id or f"goal-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            title=request.title,
            description=request.description,
            status="proposed",
            priority=request.priority,
            risk_level=request.risk_level,
            owner_scope=request.owner_scope,
            constraints=request.constraints,
            success_criteria=request.success_criteria,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
            completed_at=None,
            cancelled_at=None,
        )
        saved = self._save_goal(goal)
        self._record_event(
            TaskLifecycleEvent(
                lifecycle_event_id=f"lifecycle-{saved.goal_id}-created",
                task_id=None,
                goal_id=saved.goal_id,
                trace_id=saved.trace_id,
                event_type="goal_created",
                from_status=None,
                to_status=saved.status,
                reason=None,
                payload={"title": saved.title},
                created_at=now,
            )
        )
        self._emit_goal(saved, "goal_created", 0.5)
        return saved

    def get_goal(self, goal_id: str, scope: list[str]) -> GoalRecord | None:
        """Return a goal after policy and scope checks."""
        self._authorize_read(goal_id, scope)
        goal = _get_goal(self._repository, goal_id)
        if goal is None or not _within_scope(goal.owner_scope, scope):
            return None
        return goal

    def list_goals(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[GoalRecord]:
        """List goals after policy checks."""
        self._authorize_read(None, scope)
        list_goals = getattr(self._repository, "list_goals", None)
        if callable(list_goals):
            result = list_goals(scope=scope, status=status, limit=limit)
            if isinstance(result, list):
                return [goal for goal in result if isinstance(goal, GoalRecord)]
        return []

    def transition_goal(self, request: GoalTransitionRequest) -> GoalRecord:
        """Transition a goal lifecycle status."""
        goal = _get_goal(self._repository, request.goal_id)
        if goal is None:
            raise ValueError("goal_not_found")
        decision = self._authorize(
            action_type="goal.transition",
            resource_id=request.goal_id,
            risk_level=goal.risk_level,
            trace_id=goal.trace_id,
            actor_id=request.actor_id or goal.actor_id,
            workspace_id=goal.workspace_id,
            scope=goal.owner_scope,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        require_valid_goal_transition(goal.status, request.to_status)
        now = datetime.now(UTC)
        updated = goal.model_copy(
            update={
                "status": request.to_status,
                "metadata": {**goal.metadata, **request.metadata},
                "updated_at": now,
                "completed_at": now if request.to_status == "completed" else goal.completed_at,
                "cancelled_at": now if request.to_status == "cancelled" else goal.cancelled_at,
            }
        )
        saved = self._save_goal(updated)
        self._record_event(
            TaskLifecycleEvent(
                lifecycle_event_id=f"lifecycle-{saved.goal_id}-{uuid4().hex}",
                task_id=None,
                goal_id=saved.goal_id,
                trace_id=saved.trace_id,
                event_type="goal_transitioned",
                from_status=goal.status,
                to_status=saved.status,
                reason=request.reason,
                payload={"actor_id": request.actor_id, "metadata": request.metadata},
                created_at=now,
            )
        )
        self._emit_goal(saved, "goal_transitioned", 0.7)
        return saved

    def _authorize_read(self, goal_id: str | None, scope: list[str]) -> None:
        decision = self._authorize(
            action_type="goal.read",
            resource_id=goal_id,
            risk_level="low",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            context={},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")

    def _authorize(
        self,
        *,
        action_type: str,
        resource_id: str | None,
        risk_level: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="goal",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _save_goal(self, goal: GoalRecord) -> GoalRecord:
        save_goal = getattr(self._repository, "save_goal", None)
        if callable(save_goal):
            result = save_goal(goal)
            if isinstance(result, GoalRecord):
                return result
        return goal

    def _record_event(self, event: TaskLifecycleEvent) -> None:
        save_event = getattr(self._repository, "save_lifecycle_event", None)
        if callable(save_event):
            save_event(event)
        if self._publisher is not None:
            self._publisher.publish(event)

    def _emit_goal(self, goal: GoalRecord, event_type: str, intensity: float) -> None:
        _emit(
            self._telemetry_service,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{goal.goal_id}-{event_type}",
                trace_id=goal.trace_id or goal.goal_id,
                event_type=event_type,  # type: ignore[arg-type]
                node_type="goal",
                node_id=goal.goal_id,
                edge_from=goal.trace_id,
                edge_to=goal.goal_id,
                intensity=intensity,
                payload={"status": goal.status},
                created_at=datetime.now(UTC),
            ),
        )


def _get_goal(repository: object, goal_id: str) -> GoalRecord | None:
    get_goal = getattr(repository, "get_goal", None)
    if callable(get_goal):
        result = get_goal(goal_id)
        if isinstance(result, GoalRecord) or result is None:
            return result
    return None


def _within_scope(owner_scope: list[str], scope: list[str]) -> bool:
    return not scope or any(item in owner_scope for item in scope)


def _emit(telemetry_service: object | None, event: VisualTelemetryEvent) -> None:
    if telemetry_service is None:
        return
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
