"""Attention API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.attention import (
    get_attention_controller,
    get_context_budgeter,
    get_focus_service,
    get_interrupt_router,
)
from aion_brain.contracts.attention import (
    ContextBudget,
    InterruptRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.test_attention_contracts import attention_decision, attention_signal, focus_session


class FakeAttentionController:
    def create_signal(self, request):
        return attention_signal(attention_signal_id="signal-api", owner_scope=request.owner_scope)

    def list_signals(self, scope, handled=None, limit=100):
        return [attention_signal(attention_signal_id="signal-api", owner_scope=scope)]

    def decide(self, request):
        return attention_decision(attention_decision_id="decision-api", priority_score=0.7)

    def mark_signal_handled(self, attention_signal_id, scope):
        return attention_signal(attention_signal_id=attention_signal_id, owner_scope=scope)


class FakeFocusService:
    def create_focus_session(self, request):
        return focus_session(focus_session_id="focus-api", owner_scope=request.owner_scope)

    def get_active_focus(self, actor_id, workspace_id, scope):
        return focus_session(focus_session_id="focus-active", owner_scope=scope)

    def get_focus_session(self, focus_session_id, scope):
        return focus_session(focus_session_id=focus_session_id, owner_scope=scope)

    def list_focus_sessions(self, scope, status=None, limit=50):
        return [focus_session(focus_session_id="focus-api", owner_scope=scope)]

    def transition_focus(self, request):
        return focus_session(focus_session_id=request.focus_session_id, status=request.to_status)


class FakeInterruptRouter:
    def create_interrupt(self, request):
        return interrupt_record(interrupt_id="interrupt-api")

    def list_interrupts(self, scope, status=None, limit=50):
        return [interrupt_record(interrupt_id="interrupt-api")]

    def decide_interrupt(self, request):
        return interrupt_record(interrupt_id=request.interrupt_id, status="accepted")


class FakeBudgeter:
    def allocate(self, request):
        return ContextBudget(
            context_budget_id="budget-api",
            trace_id=request.trace_id,
            focus_session_id=request.focus_session_id,
            intent_id=request.intent_id,
            context_id=request.context_id,
            max_items=request.max_items,
            max_chars=request.max_chars,
            allocation={"working_memory": 1},
            used_items=0,
            used_chars=0,
            overflow_items=[],
            constraints=[],
            created_at=datetime.now(UTC),
        )


def test_attention_focus_interrupt_and_budget_routes_work() -> None:
    """Attention control routes return public contracts."""
    app.dependency_overrides[get_attention_controller] = lambda: FakeAttentionController()
    app.dependency_overrides[get_focus_service] = lambda: FakeFocusService()
    app.dependency_overrides[get_interrupt_router] = lambda: FakeInterruptRouter()
    app.dependency_overrides[get_context_budgeter] = lambda: FakeBudgeter()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        signal = client.post(
            "/brain/attention/signals",
            json={
                "signal_type": "generic",
                "source_type": "event",
                "title": "Generic signal",
                "payload": {},
            },
        )
        signals = client.get("/brain/attention/signals", params={"scope": "workspace:main"})
        decision = client.post(
            "/brain/attention/decide",
            json={"goal": "continue", "scope": ["workspace:main"]},
        )
        handled = client.post(
            "/brain/attention/signals/signal-api/handled",
            params={"scope": "workspace:main"},
        )
        focus = client.post(
            "/brain/focus",
            json={"title": "Focus", "description": "Generic focus"},
        )
        active = client.get("/brain/focus/active", params={"scope": "workspace:main"})
        focus_get = client.get("/brain/focus/focus-api", params={"scope": "workspace:main"})
        focus_list = client.get("/brain/focus", params={"scope": "workspace:main"})
        transition = client.post(
            "/brain/focus/focus-api/transition",
            json={"focus_session_id": "focus-api", "to_status": "paused", "reason": "pause"},
        )
        interrupt = client.post(
            "/brain/interrupts",
            json={
                "interrupt_type": "generic",
                "source_type": "event",
                "payload": {},
            },
        )
        interrupts = client.get("/brain/interrupts", params={"scope": "workspace:main"})
        interrupt_decision = client.post(
            "/brain/interrupts/interrupt-api/decide",
            json={"interrupt_id": "interrupt-api", "decision": "accept", "reason": "accept"},
        )
        budget = client.post(
            "/brain/context-budget/allocate",
            json={"scope": ["workspace:main"], "requested_sources": ["working_memory"]},
        )
    finally:
        app.dependency_overrides.clear()

    for response in (
        signal,
        signals,
        decision,
        handled,
        focus,
        active,
        focus_get,
        focus_list,
        transition,
        interrupt,
        interrupts,
        interrupt_decision,
        budget,
    ):
        assert response.status_code == 200
    assert decision.json()["attention_decision_id"] == "decision-api"
    assert budget.json()["context_budget_id"] == "budget-api"


def interrupt_record(**updates: object) -> InterruptRecord:
    payload = {
        "interrupt_id": "interrupt-1",
        "trace_id": "trace-1",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "focus_session_id": None,
        "interrupt_type": "generic",
        "source_type": "event",
        "source_id": "event-1",
        "status": "pending",
        "priority_score": 0.5,
        "payload": {},
        "decision": {},
        "created_at": datetime.now(UTC),
        "resolved_at": None,
    }
    payload.update(updates)
    return InterruptRecord.model_validate(payload)


def actor_context() -> ActorContext:
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["owner"],
        permissions=["trace.read"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )
