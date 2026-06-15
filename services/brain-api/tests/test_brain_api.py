"""Brain API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.brain import get_brain_loop_service
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.main import app


class FakeRuntime:
    """Runtime fake for API tests."""

    def think(self, event: AIONEvent) -> DecisionTrace:
        """Return a deterministic trace for the full loop service dependency."""
        return self.run(event)

    def run(self, event: AIONEvent) -> DecisionTrace:
        return DecisionTrace(
            trace_id=event.trace_id or f"trace-{event.event_id}",
            event_id=event.event_id,
            intent_id="intent-1",
            context_id="context-1",
            plan_id="plan-1",
            memory_refs=[],
            capability_refs=[],
            policy_decisions=[],
            outcome={
                "status": "planned",
                "runtime": "langgraph",
                "message": "AION Brain completed deterministic planning loop.",
            },
            created_at=datetime.now(UTC),
        )


def test_brain_plan_api_returns_plan_graph() -> None:
    """POST /brain/plan returns a deterministic PlanGraph."""
    response = TestClient(app).post(
        "/brain/plan",
        json={
            "context": {
                "context_id": "context-1",
                "intent_id": "intent-1",
                "goal": "answer a generic question",
                "known_context": [{"source": "intent", "intent_type": "question.answer"}],
                "retrieved_memory_ids": [],
                "available_capability_ids": [],
                "constraints": [],
                "open_questions": [],
                "execution_limits": {"no_model_calls": True},
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan_id"] == "plan-intent-1"
    assert [step["step_id"] for step in body["steps"]] == [
        "retrieve_context",
        "draft_response",
        "evaluate_response",
    ]


def test_brain_think_api_returns_decision_trace() -> None:
    """POST /brain/think returns a public DecisionTrace."""
    app.dependency_overrides[get_brain_loop_service] = lambda: FakeRuntime()
    try:
        response = TestClient(app).post("/brain/think", json=event_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["outcome"]["status"] == "planned"
    assert response.json()["outcome"]["runtime"] == "langgraph"


def event_payload() -> dict[str, object]:
    """Return a valid event payload."""
    return {
        "event_id": "event-1",
        "source": "test",
        "event_type": "question.answer",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "payload_type": "test.payload",
        "payload": {"question": "what should happen?"},
        "timestamp": datetime.now(UTC).isoformat(),
        "correlation_id": "corr-1",
        "trace_id": "trace-1",
        "security_scope": ["workspace:main"],
    }
