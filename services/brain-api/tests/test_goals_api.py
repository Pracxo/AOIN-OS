"""Goal Manager API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_goal_service
from aion_brain.contracts.goals import GoalCreateRequest, GoalRecord, GoalTransitionRequest
from aion_brain.main import app


class FakeGoalService:
    """Goal service fake for API tests."""

    def __init__(self) -> None:
        self.goals: dict[str, GoalRecord] = {
            "goal-1": make_goal("goal-1"),
        }

    def create_goal(self, request: GoalCreateRequest) -> GoalRecord:
        goal = make_goal(request.goal_id or "goal-created", title=request.title)
        self.goals[goal.goal_id] = goal
        return goal

    def get_goal(self, goal_id: str, scope: list[str]) -> GoalRecord | None:
        goal = self.goals.get(goal_id)
        if goal and any(item in goal.owner_scope for item in scope):
            return goal
        return None

    def list_goals(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[GoalRecord]:
        return [
            goal
            for goal in self.goals.values()
            if any(item in goal.owner_scope for item in scope)
            and (status is None or goal.status == status)
        ][:limit]

    def transition_goal(self, request: GoalTransitionRequest) -> GoalRecord:
        goal = self.goals[request.goal_id].model_copy(update={"status": request.to_status})
        self.goals[goal.goal_id] = goal
        return goal


def test_goals_api_create_get_list_and_transition() -> None:
    """Goal endpoints expose generic lifecycle records."""
    service = FakeGoalService()
    app.dependency_overrides[get_goal_service] = lambda: service
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/goals",
            json={
                "goal_id": "goal-created",
                "title": "Goal",
                "description": "Goal description",
                "owner_scope": ["workspace:main"],
            },
        )
        fetched = client.get("/brain/goals/goal-created", params={"scope": "workspace:main"})
        listed = client.get("/brain/goals", params={"scope": "workspace:main"})
        transitioned = client.post(
            "/brain/goals/goal-created/transition",
            json={"to_status": "active", "reason": "ready"},
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert created.json()["goal_id"] == "goal-created"
    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert listed.json()[0]["goal_id"] == "goal-1"
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "active"


def test_goals_api_rejects_invalid_transition_status() -> None:
    """Invalid goal statuses are rejected by API validation."""
    app.dependency_overrides[get_goal_service] = lambda: FakeGoalService()
    try:
        response = TestClient(app).post(
            "/brain/goals/goal-1/transition",
            json={"to_status": "running"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def make_goal(goal_id: str, *, title: str = "Goal") -> GoalRecord:
    """Create a goal record."""
    now = datetime.now(UTC)
    return GoalRecord(
        goal_id=goal_id,
        title=title,
        description="Goal description",
        status="proposed",
        priority="normal",
        risk_level="medium",
        owner_scope=["workspace:main"],
        created_at=now,
        updated_at=now,
    )
