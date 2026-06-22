"""Goal Manager service tests."""

import pytest

from aion_brain.contracts.goals import GoalCreateRequest, GoalRecord, GoalTransitionRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.tasks import TaskLifecycleEvent
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.goals.service import GoalService
from aion_brain.tasks.publisher import NoopTaskLifecyclePublisher


class FakePolicyAdapter:
    """Policy fake for goal service tests."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeGoalRepository:
    """In-memory goal repository fake."""

    def __init__(self) -> None:
        self.goals: dict[str, GoalRecord] = {}
        self.events: list[TaskLifecycleEvent] = []

    def save_goal(self, goal: GoalRecord) -> GoalRecord:
        self.goals[goal.goal_id] = goal
        return goal

    def get_goal(self, goal_id: str) -> GoalRecord | None:
        return self.goals.get(goal_id)

    def list_goals(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[GoalRecord]:
        goals = [
            goal
            for goal in self.goals.values()
            if (not scope or any(item in goal.owner_scope for item in scope))
            and (status is None or goal.status == status)
        ]
        return goals[:limit]

    def save_lifecycle_event(self, event: TaskLifecycleEvent) -> TaskLifecycleEvent:
        self.events.append(event)
        return event


class FakeTelemetry:
    """Telemetry fake for goal service tests."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_goal_service_creates_goal_records_events_and_telemetry() -> None:
    """Creating a goal persists the record and lifecycle event."""
    repository = FakeGoalRepository()
    policy = FakePolicyAdapter()
    publisher = NoopTaskLifecyclePublisher(published=False)
    telemetry = FakeTelemetry()
    service = GoalService(
        repository=repository,
        policy_adapter=policy,
        publisher=publisher,
        telemetry_service=telemetry,
    )

    goal = service.create_goal(
        GoalCreateRequest(
            goal_id="goal-1",
            trace_id="trace-1",
            actor_id="actor-1",
            workspace_id="workspace-1",
            title="Hold a generic goal",
            description="Track the lifecycle of a generic goal.",
            owner_scope=["workspace:main"],
        )
    )

    assert goal.status == "proposed"
    assert repository.goals["goal-1"] == goal
    assert repository.events[0].event_type == "goal_created"
    assert publisher.events[0].goal_id == "goal-1"
    assert telemetry.events[0].event_type == "goal_created"
    assert policy.requests[0].action_type == "goal.create"


def test_goal_service_transitions_goal_through_state_machine() -> None:
    """Transitioning a goal records the lifecycle movement."""
    repository = FakeGoalRepository()
    service = GoalService(
        repository=repository,
        policy_adapter=FakePolicyAdapter(),
        publisher=NoopTaskLifecyclePublisher(),
    )
    service.create_goal(
        GoalCreateRequest(
            goal_id="goal-1",
            title="Goal",
            description="Goal description",
            owner_scope=["workspace:main"],
        )
    )

    updated = service.transition_goal(
        GoalTransitionRequest(
            goal_id="goal-1",
            to_status="active",
            reason="ready",
            actor_id="actor-1",
            metadata={"phase": "started"},
        )
    )

    assert updated.status == "active"
    assert updated.metadata["phase"] == "started"
    assert repository.events[-1].event_type == "goal_transitioned"
    assert repository.events[-1].from_status == "proposed"
    assert repository.events[-1].to_status == "active"


def test_goal_service_policy_deny_blocks_create() -> None:
    """Policy denial blocks goal creation before persistence."""
    repository = FakeGoalRepository()
    service = GoalService(
        repository=repository,
        policy_adapter=FakePolicyAdapter(deny_action="goal.create"),
    )

    with pytest.raises(ValueError, match="policy_denied"):
        service.create_goal(
            GoalCreateRequest(
                goal_id="goal-1",
                title="Goal",
                description="Goal description",
                owner_scope=["workspace:main"],
            )
        )

    assert repository.goals == {}
