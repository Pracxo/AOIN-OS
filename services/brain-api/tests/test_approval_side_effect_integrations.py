"""Approval control-plane integration tests for side-effect boundaries."""

from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.contracts.approvals import ApprovalRequest
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.guardrails import GuardrailDecision, RiskGuardrailEvaluation
from aion_brain.contracts.mcp import (
    MCPInvocationRequest,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
)
from aion_brain.contracts.modules import CapabilityInvocationRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessment
from aion_brain.mcp.repository import MCPRepository
from aion_brain.mcp.service import MCPService
from aion_brain.model_gateway.budget import ModelBudgetGuard
from aion_brain.model_gateway.profile_registry import ModelProfileRegistry
from aion_brain.model_gateway.provider_registry import ModelProviderRegistry
from aion_brain.model_gateway.redaction import PromptRedactor
from aion_brain.model_gateway.repository import ModelGatewayRepository
from aion_brain.model_gateway.router import ModelGatewayRouter
from aion_brain.model_gateway.service import ModelGatewayService
from aion_brain.modules.local_internal_runtime import LocalInternalRuntimeAdapter
from aion_brain.modules.repository import ModuleRuntimeRepository
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from tests.model_gateway_fakes import (
    external_profile,
    external_provider,
    gateway_request,
)
from tests.test_mcp_contracts import invocation_payload, server_payload
from tests.test_runtime_gateway import (
    binding_request,
    registration_request,
)


class AllowPolicy:
    """Policy fake."""

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


class FakeApprovalService:
    """Approval service fake that always requests approval."""

    def __init__(self) -> None:
        self.calls = 0

    def evaluate_and_maybe_request(self, request: object) -> RiskGuardrailEvaluation:
        self.calls += 1
        return RiskGuardrailEvaluation(
            risk_assessment=risk_assessment(),
            guardrail_decision=guardrail_decision(),
            approval_request=approval_request(),
            final_decision="require_approval",
            reason="approval_required",
            created_at=datetime.now(UTC),
        )


class CountingAdapter(LocalInternalRuntimeAdapter):
    """Runtime adapter that records calls."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, request: object, runtime: object) -> object:
        self.calls += 1
        return super().invoke(request, runtime)  # type: ignore[arg-type]


class CountingModelAdapter(DeterministicReasoningAdapter):
    """Model adapter that records calls."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: object, route: object) -> object:
        self.calls += 1
        return super().complete(prompt, route)  # type: ignore[arg-type]


def test_model_gateway_requires_approval_before_external_model_call() -> None:
    """External model gateway use creates approval and does not call adapter."""
    repo = ModelGatewayRepository(engine=sqlite_engine())
    policy = AllowPolicy()
    provider_registry = ModelProviderRegistry(repo, policy)
    profile_registry = ModelProfileRegistry(repo, policy)
    repo.save_provider(external_provider())
    repo.save_profile(
        external_profile().model_copy(
            update={"cost_per_1k_input_tokens": 0.0, "cost_per_1k_output_tokens": 0.0}
        )
    )
    adapter = CountingModelAdapter()
    approval_service = FakeApprovalService()
    service = ModelGatewayService(
        provider_registry=provider_registry,
        profile_registry=profile_registry,
        router=ModelGatewayRouter(),
        redactor=PromptRedactor(),
        budget_guard=ModelBudgetGuard(repo),
        adapters={"deterministic": DeterministicReasoningAdapter(), "litellm_http": adapter},
        policy_adapter=policy,
        repository=repo,
        model_gateway_enabled=True,
        approval_service=approval_service,
    )
    request = gateway_request().model_copy(
        update={
            "preferred_profile_id": "external-profile",
            "allow_external": True,
            "metadata": {"permissions": ["model.external.use"]},
        }
    )

    response = service.complete(request)

    assert response.status == "blocked_by_policy"
    assert response.reason == "approval_required"
    assert approval_service.calls == 1
    assert adapter.calls == 0


def test_runtime_gateway_requires_approval_before_controlled_capability_call() -> None:
    """Controlled high-risk capability invocation does not call runtime while pending."""
    registry = CapabilityRegistry()
    registry.register(manifest())
    repo = ModuleRuntimeRepository(engine=sqlite_engine())
    adapter = CountingAdapter()
    approval_service = FakeApprovalService()
    gateway = CapabilityRuntimeGateway(
        module_runtime_repository=repo,
        capability_registry=registry,
        policy_adapter=AllowPolicy(),
        runtime_adapters={"local_internal": adapter},
        approval_service=approval_service,
    )
    gateway.register_runtime(registration_request())
    gateway.bind_capability(binding_request("controlled"))

    result = gateway.invoke(
        CapabilityInvocationRequest(
            invocation_id="invocation-1",
            trace_id="trace-1",
            capability_id="aion.internal.noop",
            mode="controlled",
            payload={},
            metadata={"risk_level": "high", "security_scope": ["workspace:main"]},
        )
    )

    assert result.status == "blocked_by_policy"
    assert result.error["approval_request_id"] == "approval-1"
    assert approval_service.calls == 1
    assert adapter.calls == 0


def test_mcp_service_requires_approval_before_controlled_tool_call() -> None:
    """Controlled MCP invocation stops before fake tool execution when approval is pending."""
    approval_service = FakeApprovalService()
    service = MCPService(
        mcp_repository=MCPRepository(engine=sqlite_engine()),
        capability_service=None,
        policy_adapter=AllowPolicy(),
        telemetry_service=None,
        settings=SimpleNamespace(
            mcp_enabled=True,
            mcp_allow_network=False,
            mcp_allow_stdio=False,
            mcp_timeout_seconds=15.0,
            mcp_default_risk_level="medium",
            mcp_auto_register_capabilities=False,
        ),
        approval_service=approval_service,
    )
    service.register_server(
        MCPServerRegistrationRequest(
            server=service_server(),
            activate=True,
            discover_tools=False,
        )
    )
    service.sync_tools(
        MCPSyncRequest(
            mcp_server_id="mcp-server-1",
            dry_run=False,
            auto_register_capabilities=True,
            default_risk_level="medium",
            default_permissions_required=[],
            owner_scope=["workspace:main"],
        )
    )

    result = service.invoke(
        MCPInvocationRequest(
            **{
                **invocation_payload(),
                "capability_id": "mcp.test-server.echo",
                "mode": "controlled",
                "payload": {"value": 1},
            }
        )
    )

    assert result.status == "blocked_by_policy"
    assert result.error["approval_request_id"] == "approval-1"
    assert approval_service.calls == 1


def sqlite_engine():
    """Return a shared in-memory engine."""
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def manifest() -> CapabilityManifest:
    """Return a generic module manifest."""
    return CapabilityManifest(
        module_id="test.module",
        version="0.1.0",
        capabilities=[{"capability_id": "aion.internal.noop", "name": "Noop"}],
        permissions_required=[],
        memory_read_scopes=[],
        memory_write_scopes=[],
        events_subscribed=[],
        events_published=[],
        execution_mode="sync",
    )


def risk_assessment() -> RiskAssessment:
    """Return a risk assessment."""
    return RiskAssessment(
        risk_assessment_id="risk-1",
        trace_id="trace-1",
        action_type="capability.invoke",
        resource_type="capability",
        requested_risk_level="high",
        computed_risk_level="high",
        risk_score=0.8,
        factors=[],
        constraints=["approval_required"],
        decision="require_approval",
        metadata={"security_scope": ["workspace:main"]},
    )


def guardrail_decision() -> GuardrailDecision:
    """Return a guardrail decision."""
    return GuardrailDecision(
        guardrail_decision_id="guardrail-decision-1",
        action_type="capability.invoke",
        resource_type="capability",
        matched_guardrails=["guardrail-1"],
        allow=False,
        approval_required=True,
        blocked=False,
        severity="high",
        reason="guardrail_requires_approval",
        constraints=["approval_required"],
        metadata={},
    )


def approval_request() -> ApprovalRequest:
    """Return an approval request."""
    return ApprovalRequest(
        approval_request_id="approval-1",
        action_type="capability.invoke",
        resource_type="capability",
        title="Review",
        description="Review generic action.",
        status="pending",
        priority="normal",
        approval_scope=["workspace:main"],
        payload={},
        constraints=[],
    )


def service_server():
    """Return an MCP server record."""
    from aion_brain.contracts.mcp import MCPServerRecord

    return MCPServerRecord(**server_payload())
