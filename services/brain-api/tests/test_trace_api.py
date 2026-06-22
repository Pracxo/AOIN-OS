"""Trace API tests."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.api.brain import get_brain_loop_service
from aion_brain.api.dependencies import get_audit_repository
from aion_brain.audit.ledger import AuditLedger
from aion_brain.audit.repository import AuditRepository
from aion_brain.context.compiler import ContextCompiler, EmptyCapabilityCatalog
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.intent.engine import IntentEngine
from aion_brain.learning.engine import LearningEngine
from aion_brain.main import app
from aion_brain.planning.planner import Planner
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter
from aion_brain.telemetry.visual import VisualTelemetryBuilder


class FakePolicyAdapter:
    """Policy fake for trace API tests."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}-{request.resource_id or 'root'}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


@pytest.fixture
def repository() -> AuditRepository:
    """Create an isolated repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return AuditRepository(engine=engine)


@pytest.fixture
def client(repository: AuditRepository) -> TestClient:
    """Create a test client with audit and Brain loop dependencies overridden."""
    policy = FakePolicyAdapter()
    runtime = LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy,
            capability_catalog=EmptyCapabilityCatalog(),
        ),
        planner=Planner(),
        policy_adapter=policy,
    )
    service = BrainLoopService(
        runtime=runtime,
        audit_ledger=AuditLedger(repository),
        evaluator=Evaluator(),
        learning_engine=LearningEngine(),
        telemetry_builder=VisualTelemetryBuilder(),
    )
    app.dependency_overrides[get_audit_repository] = lambda: repository
    app.dependency_overrides[get_brain_loop_service] = lambda: service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_brain_think_persists_trace_evaluation_learning_and_telemetry(
    client: TestClient,
) -> None:
    """POST /brain/think persists the full deterministic Brain loop outputs."""
    think_response = client.post("/brain/think", json=event_payload())
    trace_id = think_response.json()["trace_id"]

    trace_response = client.get(f"/brain/traces/{trace_id}")
    evaluation_response = client.get(f"/brain/traces/{trace_id}/evaluation")
    learning_response = client.get(f"/brain/traces/{trace_id}/learning")
    telemetry_response = client.get(f"/brain/traces/{trace_id}/telemetry")

    assert think_response.status_code == 200
    assert trace_response.status_code == 200
    assert trace_response.json()["trace_id"] == trace_id
    assert evaluation_response.status_code == 200
    assert learning_response.status_code == 200
    assert learning_response.json()[0]["promotion_status"] == "candidate"
    assert telemetry_response.status_code == 200
    assert {event["event_type"] for event in telemetry_response.json()} >= {
        "brain_loop_started",
        "trace_created",
        "evaluation_completed",
        "learning_signal_created",
        "brain_loop_completed",
    }


def test_evaluate_and_learn_apis_work(client: TestClient) -> None:
    """POST /brain/evaluate and POST /brain/learn return public contracts."""
    trace = client.post("/brain/think", json=event_payload("event-2", "trace-2")).json()
    evaluation = client.post("/brain/evaluate", json=trace).json()
    signal = client.post("/brain/learn", json={"trace": trace, "evaluation": evaluation}).json()

    assert evaluation["trace_id"] == "trace-2"
    assert signal["trace_id"] == "trace-2"
    assert signal["promotion_status"] == "candidate"


def event_payload(event_id: str = "event-1", trace_id: str = "trace-1") -> dict[str, object]:
    """Return a valid event payload."""
    return {
        "event_id": event_id,
        "source": "test",
        "event_type": "question.answer",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "payload_type": "test.payload",
        "payload": {"question": "what should happen?"},
        "timestamp": datetime.now(UTC).isoformat(),
        "correlation_id": "corr-1",
        "trace_id": trace_id,
        "security_scope": ["workspace:main"],
    }
