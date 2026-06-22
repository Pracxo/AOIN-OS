"""Shared fakes and factories for model gateway tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.model_gateway import ModelGatewayRequest, ModelProfile, ModelProvider
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reasoning import ModelCallRecord, ModelRouteDecision, PromptPacket
from aion_brain.model_gateway.budget import ModelBudgetGuard
from aion_brain.model_gateway.profile_registry import ModelProfileRegistry, deterministic_profile
from aion_brain.model_gateway.provider_registry import (
    ModelProviderRegistry,
    deterministic_provider,
)
from aion_brain.model_gateway.redaction import PromptRedactor
from aion_brain.model_gateway.repository import ModelGatewayRepository
from aion_brain.model_gateway.router import ModelGatewayRouter
from aion_brain.model_gateway.service import ModelGatewayService
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter


class AllowPolicy:
    """Policy fake that allows every action and records requests."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy(AllowPolicy):
    """Policy fake that denies one action."""

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self.action_type = action_type

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.action_type
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=not allow,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["blocked"],
            audit_level="standard" if allow else "high",
        )


class FakeTelemetry:
    """Collect emitted telemetry events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeObservability:
    """Collect observability events."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.events: list[object] = []

    def record_event(self, event: object) -> object:
        if self.fail:
            raise RuntimeError("observability failed")
        self.events.append(event)
        return event


class FailingAdapter:
    """Adapter fake that returns a failed model call."""

    def complete(self, prompt: PromptPacket, route: ModelRouteDecision) -> ModelCallRecord:
        return ModelCallRecord(
            model_call_id=f"model-call-{prompt.prompt_id}",
            trace_id=prompt.trace_id,
            reasoning_id=route.reasoning_id,
            provider=route.selected_provider,
            model=route.selected_model,
            mode=route.mode,
            request={"prompt_id": prompt.prompt_id},
            response={"reason": "provider_failed"},
            status="failed",
            latency_ms=None,
            cost_estimate=0.0,
            created_at=datetime.now(UTC),
        )


def repository() -> ModelGatewayRepository:
    """Return an in-memory repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ModelGatewayRepository(engine=engine)


def model_gateway_service(
    *,
    policy: AllowPolicy | None = None,
    block_on_secret: bool = True,
    telemetry: FakeTelemetry | None = None,
    adapters: dict[str, object] | None = None,
    gateway_enabled: bool = False,
) -> tuple[ModelGatewayService, ModelGatewayRepository, AllowPolicy, FakeTelemetry]:
    """Return a local model gateway service and its supporting fakes."""
    repo = repository()
    selected_policy = policy or AllowPolicy()
    selected_telemetry = telemetry or FakeTelemetry()
    provider_registry = ModelProviderRegistry(repo, selected_policy)
    profile_registry = ModelProfileRegistry(repo, selected_policy)
    provider_registry.ensure_defaults()
    profile_registry.ensure_defaults()
    service = ModelGatewayService(
        provider_registry=provider_registry,
        profile_registry=profile_registry,
        router=ModelGatewayRouter(),
        redactor=PromptRedactor(block_on_secret=block_on_secret),
        budget_guard=ModelBudgetGuard(repo),
        adapters={
            "deterministic": DeterministicReasoningAdapter(),
            **(adapters or {}),
        },
        policy_adapter=selected_policy,
        repository=repo,
        telemetry_service=selected_telemetry,
        observability_service=FakeObservability(),
        model_gateway_enabled=gateway_enabled,
    )
    return service, repo, selected_policy, selected_telemetry


def prompt(text: str = "answer a generic question") -> PromptPacket:
    """Return a prompt packet."""
    return PromptPacket(
        prompt_id="prompt-1",
        trace_id="trace-1",
        intent_id="intent-1",
        context_id="context-1",
        goal=text,
        system_instructions=["Use AION contracts."],
        context_items=[
            {"type": "known_context", "value": [{"source": "intent"}]},
            {"type": "retrieved_memory_ids", "value": ["memory-1"]},
            {"type": "available_capability_ids", "value": ["capability-1"]},
            {"type": "open_questions", "value": []},
        ],
        constraints=[],
        requested_output_schema={},
        token_budget_hint=None,
        created_at=datetime.now(UTC),
    )


def gateway_request(text: str = "answer a generic question") -> ModelGatewayRequest:
    """Return a model gateway request."""
    return ModelGatewayRequest(
        request_id="request-1",
        trace_id="trace-1",
        reasoning_id="reasoning-1",
        prompt=prompt(text),
        mode="analyze",
        risk_level="low",
        actor_id="actor-1",
        workspace_id="workspace-1",
        scope=["workspace:main"],
        preferred_profile_id=None,
        allow_external=False,
        metadata={},
    )


def external_provider() -> ModelProvider:
    """Return an external HTTP provider contract."""
    return ModelProvider(
        provider_id="external-provider",
        provider_type="litellm_http",
        display_name="External Provider",
        status="active",
        endpoint_ref="http://example.invalid",
        config={},
        health_status="healthy",
    )


def external_profile() -> ModelProfile:
    """Return an external profile contract."""
    return ModelProfile(
        model_profile_id="external-profile",
        provider_id="external-provider",
        model_name="external-generic-model",
        mode="analyze",
        status="active",
        privacy_level="external",
        risk_level="low",
        max_input_tokens=8000,
        max_output_tokens=1000,
        cost_per_1k_input_tokens=1.0,
        cost_per_1k_output_tokens=1.0,
        latency_class="medium",
        metadata={},
    )


def deterministic_provider_contract() -> ModelProvider:
    """Return deterministic provider contract."""
    return deterministic_provider()


def deterministic_profile_contract() -> ModelProfile:
    """Return deterministic profile contract."""
    return deterministic_profile()
