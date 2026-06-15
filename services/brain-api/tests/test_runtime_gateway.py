"""CapabilityRuntimeGateway tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine

from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.modules import (
    CapabilityBindingRequest,
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    ModuleRuntime,
    ModuleRuntimeRegistrationRequest,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.modules.local_internal_runtime import LocalInternalRuntimeAdapter
from aion_brain.modules.repository import ModuleRuntimeRepository
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway


class FakePolicyAdapter:
    """Policy fake for runtime gateway tests."""

    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard" if self.allow else "high",
        )


class FakeTelemetry:
    """Telemetry fake."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


class CountingRuntimeAdapter(LocalInternalRuntimeAdapter):
    """Runtime adapter that records invocation count."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(
        self,
        request: CapabilityInvocationRequest,
        runtime: ModuleRuntime,
    ) -> CapabilityInvocationResult:
        self.calls += 1
        return super().invoke(request, runtime)


def test_runtime_gateway_registration_requires_policy() -> None:
    """Runtime registration asks policy and persists an approved runtime."""
    policy = FakePolicyAdapter()
    gateway = make_gateway(policy=policy)

    response = gateway.register_runtime(registration_request())

    assert response.registered is True
    assert policy.requests[0].action_type == "module.runtime.register"
    assert gateway.get_runtime("runtime-1").status == "active"  # type: ignore[union-attr]


def test_runtime_gateway_policy_deny_blocks_registration() -> None:
    """Policy denial blocks runtime registration."""
    gateway = make_gateway(policy=FakePolicyAdapter(allow=False))

    response = gateway.register_runtime(registration_request())

    assert response.registered is False
    assert response.status == "blocked_by_policy"


def test_runtime_gateway_binding_requires_capability_and_runtime() -> None:
    """Binding validates capability and runtime existence."""
    gateway = make_gateway()
    gateway.register_runtime(registration_request())

    binding = gateway.bind_capability(binding_request("controlled"))

    assert binding.capability_id == "aion.internal.noop"


def test_runtime_gateway_dry_run_does_not_call_runtime_adapter() -> None:
    """Dry-run invocation validates binding but avoids adapter invocation."""
    adapter = CountingRuntimeAdapter()
    gateway = make_gateway(runtime_adapter=adapter)
    gateway.register_runtime(registration_request())
    gateway.bind_capability(binding_request("dry_run"))

    result = gateway.invoke(invocation_request(mode="dry_run"))

    assert result.status == "dry_run"
    assert adapter.calls == 0


def test_runtime_gateway_controlled_mode_calls_local_internal_runtime() -> None:
    """Controlled invocation uses the local internal runtime adapter."""
    adapter = CountingRuntimeAdapter()
    gateway = make_gateway(runtime_adapter=adapter)
    gateway.register_runtime(registration_request())
    gateway.bind_capability(binding_request("controlled"))

    result = gateway.invoke(invocation_request(mode="controlled"))

    assert result.status == "completed"
    assert result.output["message"] == "No operation performed."
    assert adapter.calls == 1


def test_runtime_gateway_returns_capability_not_found_for_missing_capability() -> None:
    """Missing capability returns a structured gateway result."""
    result = make_gateway().invoke(
        invocation_request(capability_id="missing.capability", mode="controlled")
    )

    assert result.status == "capability_not_found"


def test_runtime_gateway_returns_runtime_not_found_for_missing_binding() -> None:
    """Missing active binding returns runtime_not_found."""
    gateway = make_gateway()
    gateway.register_runtime(registration_request())

    result = gateway.invoke(invocation_request(mode="controlled"))

    assert result.status == "runtime_not_found"


def test_runtime_gateway_returns_runtime_unhealthy() -> None:
    """Unhealthy runtime blocks invocation before adapter use."""
    gateway = make_gateway(runtime=runtime(health_status="unhealthy"))
    gateway.register_runtime(registration_request(runtime=runtime(health_status="unhealthy")))
    gateway.bind_capability(binding_request("controlled"))

    result = gateway.invoke(invocation_request(mode="controlled"))

    assert result.status == "runtime_unhealthy"


def test_runtime_gateway_health_check_updates_runtime_health_status() -> None:
    """Health checks persist and update runtime health."""
    telemetry = FakeTelemetry()
    gateway = make_gateway(telemetry=telemetry)
    gateway.register_runtime(registration_request())

    health = gateway.health_check("runtime-1")

    assert health.status == "healthy"
    assert gateway.get_runtime("runtime-1").health_status == "healthy"  # type: ignore[union-attr]
    assert "module_health_checked" in {event.event_type for event in telemetry.events}


def make_gateway(
    *,
    policy: FakePolicyAdapter | None = None,
    runtime_adapter: CountingRuntimeAdapter | None = None,
    runtime: ModuleRuntime | None = None,
    telemetry: FakeTelemetry | None = None,
) -> CapabilityRuntimeGateway:
    """Create a runtime gateway with an in-memory database."""
    registry = CapabilityRegistry()
    registry.register(manifest())
    repository = ModuleRuntimeRepository(engine=create_engine("sqlite+pysqlite:///:memory:"))
    if runtime is not None:
        repository.save_runtime(runtime)
    adapter = runtime_adapter or CountingRuntimeAdapter()
    return CapabilityRuntimeGateway(
        module_runtime_repository=repository,
        capability_registry=registry,
        policy_adapter=policy or FakePolicyAdapter(),
        telemetry_service=telemetry,
        runtime_adapters={"local_internal": adapter},
    )


def manifest() -> CapabilityManifest:
    """Create a generic internal capability manifest."""
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


def runtime(*, health_status: str = "unknown") -> ModuleRuntime:
    """Create a module runtime."""
    return ModuleRuntime(
        runtime_id="runtime-1",
        module_id="test.module",
        version="0.1.0",
        runtime_type="local_internal",
        endpoint_ref=None,
        status="active",
        health_status=health_status,  # type: ignore[arg-type]
        config={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def registration_request(
    *,
    runtime: ModuleRuntime | None = None,
) -> ModuleRuntimeRegistrationRequest:
    """Create a runtime registration request."""
    selected_runtime = runtime or globals()["runtime"]()
    return ModuleRuntimeRegistrationRequest(runtime=selected_runtime, activate=True)


def binding_request(mode: str) -> CapabilityBindingRequest:
    """Create a binding request."""
    return CapabilityBindingRequest(
        capability_id="aion.internal.noop",
        module_id="test.module",
        runtime_id="runtime-1",
        invocation_mode=mode,  # type: ignore[arg-type]
    )


def invocation_request(
    *,
    capability_id: str = "aion.internal.noop",
    mode: str,
) -> CapabilityInvocationRequest:
    """Create a capability invocation request."""
    return CapabilityInvocationRequest(
        invocation_id="invocation-1",
        trace_id="trace-1",
        capability_id=capability_id,
        mode=mode,  # type: ignore[arg-type]
        payload={},
        approval_present=True,
    )
