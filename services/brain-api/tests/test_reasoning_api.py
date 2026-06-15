"""Reasoning API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.reasoning import get_reasoning_mesh, get_reasoning_repository
from aion_brain.contracts.reasoning import ModelCallRecord, ReasoningRequest, ReasoningResult
from aion_brain.main import app


class FakeReasoningMesh:
    """Reasoning mesh fake for API tests."""

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        return make_result(request.reasoning_id)


class FakeReasoningRepository:
    """Reasoning repository fake for API tests."""

    def get_reasoning(self, reasoning_id: str) -> ReasoningResult | None:
        if reasoning_id == "missing":
            return None
        return make_result(reasoning_id)

    def get_model_call(self, model_call_id: str) -> ModelCallRecord | None:
        if model_call_id == "missing":
            return None
        return make_model_call(model_call_id)


def test_reason_api_returns_reasoning_result() -> None:
    """POST /brain/reason returns a ReasoningResult contract."""
    app.dependency_overrides[get_reasoning_mesh] = lambda: FakeReasoningMesh()
    try:
        response = TestClient(app).post("/brain/reason", json=request_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["reasoning_id"] == "reasoning-1"


def test_get_reasoning_api_returns_persisted_result() -> None:
    """GET /brain/reason/{reasoning_id} returns persisted reasoning."""
    app.dependency_overrides[get_reasoning_repository] = lambda: FakeReasoningRepository()
    try:
        response = TestClient(app).get("/brain/reason/reasoning-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["reasoning_id"] == "reasoning-1"


def test_get_model_call_api_returns_persisted_record() -> None:
    """GET /brain/model-calls/{model_call_id} returns a ledger record."""
    app.dependency_overrides[get_reasoning_repository] = lambda: FakeReasoningRepository()
    try:
        response = TestClient(app).get("/brain/model-calls/model-call-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["model_call_id"] == "model-call-1"


def request_payload() -> dict[str, object]:
    """Return a valid reasoning request payload."""
    return {
        "reasoning_id": "reasoning-1",
        "trace_id": "trace-1",
        "intent": None,
        "context": {
            "context_id": "context-1",
            "intent_id": "intent-1",
            "goal": "answer a generic question",
            "known_context": [],
            "retrieved_memory_ids": [],
            "available_capability_ids": [],
            "constraints": [],
            "open_questions": [],
            "execution_limits": {},
        },
        "mode": "analyze",
        "risk_level": "low",
        "metadata": {},
    }


def make_result(reasoning_id: str) -> ReasoningResult:
    """Create a reasoning result."""
    route = {
        "route_id": "route-1",
        "trace_id": "trace-1",
        "reasoning_id": reasoning_id,
        "selected_provider": "deterministic",
        "selected_model": "deterministic-reasoner-v0",
        "mode": "analyze",
        "reason": "v0.1 uses deterministic local reasoning only",
        "fallback_providers": [],
        "privacy_level": "local",
        "risk_level": "low",
        "estimated_cost": 0.0,
        "estimated_latency_ms": 0,
        "created_at": datetime.now(UTC).isoformat(),
    }
    prompt = {
        "prompt_id": "prompt-1",
        "trace_id": "trace-1",
        "intent_id": "intent-1",
        "context_id": "context-1",
        "goal": "answer a generic question",
        "system_instructions": [],
        "context_items": [],
        "constraints": [],
        "requested_output_schema": {},
        "token_budget_hint": None,
        "created_at": datetime.now(UTC).isoformat(),
    }
    return ReasoningResult.model_validate(
        {
            "reasoning_id": reasoning_id,
            "trace_id": "trace-1",
            "context_id": "context-1",
            "mode": "analyze",
            "summary": "summary",
            "interpretation": "interpretation",
            "suggested_next_actions": [],
            "constraints": [],
            "confidence": 0.85,
            "requires_clarification": False,
            "clarification_questions": [],
            "route_decision": route,
            "prompt_packet": prompt,
            "metadata": {"model_call_id": "model-call-1"},
            "created_at": datetime.now(UTC).isoformat(),
        }
    )


def make_model_call(model_call_id: str) -> ModelCallRecord:
    """Create a model call record."""
    return ModelCallRecord(
        model_call_id=model_call_id,
        trace_id="trace-1",
        reasoning_id="reasoning-1",
        provider="deterministic",
        model="deterministic-reasoner-v0",
        mode="analyze",
        request={},
        response={"summary": "summary"},
        status="completed",
        latency_ms=0,
        cost_estimate=0.0,
        created_at=datetime.now(UTC),
    )
