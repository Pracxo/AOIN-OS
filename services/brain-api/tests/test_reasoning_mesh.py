"""ReasoningMesh tests."""

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reasoning import ModelCallRecord, ReasoningRequest, ReasoningResult
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from aion_brain.reasoning.mesh import ReasoningMesh
from aion_brain.reasoning.prompt_builder import PromptBuilder
from aion_brain.reasoning.router import ModelRouter


class FakePolicyAdapter:
    """Policy fake for reasoning mesh tests."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allowed = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allowed,
            approval_required=not allowed,
            reason="allowed" if allowed else "denied",
            constraints=[] if allowed else ["blocked"],
            audit_level="standard" if allowed else "high",
        )


class FakeReasoningRepository:
    """Repository fake for mesh tests."""

    def __init__(self) -> None:
        self.reasoning: list[tuple[ReasoningResult, str]] = []
        self.model_calls: list[ModelCallRecord] = []

    def save_reasoning(
        self,
        result: ReasoningResult,
        *,
        status: str = "completed",
    ) -> ReasoningResult:
        self.reasoning.append((result, status))
        return result

    def save_model_call(self, record: ModelCallRecord) -> ModelCallRecord:
        self.model_calls.append(record)
        return record


class FakeTelemetryService:
    """Telemetry fake for mesh tests."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_reasoning_mesh_authorizes_persists_and_emits() -> None:
    """Successful mesh run persists reasoning/model calls and emits telemetry."""
    policy = FakePolicyAdapter()
    repository = FakeReasoningRepository()
    telemetry = FakeTelemetryService()

    result = make_mesh(policy, repository, telemetry).reason(make_request())

    assert result.confidence >= 0.8
    assert [request.action_type for request in policy.requests] == [
        "reasoning.run",
        "model.route",
        "model.complete",
    ]
    assert repository.reasoning[0][0].reasoning_id == "reasoning-1"
    assert repository.reasoning[0][1] == "completed"
    assert repository.model_calls[0].provider == "deterministic"
    assert {event.event_type for event in telemetry.events} == {
        "reasoning_started",
        "model_route_selected",
        "model_call_recorded",
        "reasoning_completed",
    }


def test_reasoning_mesh_policy_deny_blocks_reasoning() -> None:
    """reasoning.run denial returns a blocked result without a model call."""
    policy = FakePolicyAdapter(deny_action="reasoning.run")
    repository = FakeReasoningRepository()
    telemetry = FakeTelemetryService()

    result = make_mesh(policy, repository, telemetry).reason(make_request())

    assert result.confidence == 0.0
    assert result.requires_clarification is True
    assert "reasoning_blocked_by_policy" in result.constraints
    assert repository.reasoning[0][1] == "blocked_by_policy"
    assert repository.model_calls == []
    assert [request.action_type for request in policy.requests] == ["reasoning.run"]


def make_mesh(
    policy: FakePolicyAdapter,
    repository: FakeReasoningRepository,
    telemetry: FakeTelemetryService,
) -> ReasoningMesh:
    """Create a mesh with fake dependencies."""
    return ReasoningMesh(
        model_router=ModelRouter(),
        prompt_builder=PromptBuilder(),
        model_gateway_adapter=DeterministicReasoningAdapter(),
        policy_adapter=policy,
        reasoning_repository=repository,
        telemetry_service=telemetry,
    )


def make_request() -> ReasoningRequest:
    """Create a reasoning request."""
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
