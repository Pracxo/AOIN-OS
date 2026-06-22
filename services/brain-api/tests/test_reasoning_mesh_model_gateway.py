"""ReasoningMesh integration with ModelGatewayService."""

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.reasoning import ReasoningRequest
from aion_brain.reasoning.mesh import ReasoningMesh
from aion_brain.reasoning.prompt_builder import PromptBuilder
from aion_brain.reasoning.router import ModelRouter
from tests.model_gateway_fakes import FakeTelemetry, model_gateway_service
from tests.test_reasoning_mesh import FakeReasoningRepository


def test_reasoning_mesh_works_through_model_gateway_service() -> None:
    service, _, policy, telemetry = model_gateway_service()
    repository = FakeReasoningRepository()
    mesh = ReasoningMesh(
        model_router=ModelRouter(),
        prompt_builder=PromptBuilder(),
        model_gateway_service=service,
        policy_adapter=policy,
        reasoning_repository=repository,
        telemetry_service=telemetry,
    )

    result = mesh.reason(_request())

    assert result.metadata["usage_id"]
    assert result.route_decision.selected_provider == "deterministic"
    assert repository.model_calls[0].provider == "deterministic"
    assert "model.gateway.complete" in [request.action_type for request in policy.requests]


def test_reasoning_mesh_preserves_deterministic_default() -> None:
    service, _, policy, _ = model_gateway_service(telemetry=FakeTelemetry())
    mesh = ReasoningMesh(
        model_gateway_service=service,
        policy_adapter=policy,
        reasoning_repository=FakeReasoningRepository(),
    )

    result = mesh.reason(_request())

    assert result.confidence >= 0.8
    assert result.metadata["status"] == "completed"


def _request() -> ReasoningRequest:
    return ReasoningRequest(
        reasoning_id="reasoning-1",
        trace_id="trace-1",
        intent=None,
        context=ContextPacket(
            context_id="context-1",
            intent_id="intent-1",
            goal="answer a generic question",
            known_context=[{"source": "intent"}],
            retrieved_memory_ids=["memory-1"],
            available_capability_ids=[],
            constraints=[],
            open_questions=[],
            execution_limits={},
        ),
        mode="analyze",
        risk_level="low",
        metadata={"security_scope": ["workspace:main"]},
    )
