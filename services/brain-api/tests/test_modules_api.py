"""Module and capability runtime API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_capability_runtime_gateway, get_capability_service
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.modules import (
    CapabilityBindingRequest,
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    CapabilityRuntimeBinding,
    ModuleHealthCheck,
    ModuleRuntime,
    ModuleRuntimeRegistrationRequest,
    ModuleRuntimeRegistrationResponse,
)
from aion_brain.main import app


class FakeCapabilityService:
    """Capability service fake."""

    def __init__(self) -> None:
        self.manifests: list[CapabilityManifest] = []

    def register_manifest(self, manifest: CapabilityManifest) -> CapabilityManifest:
        self.manifests.append(manifest)
        return manifest

    def list_manifests(self) -> list[CapabilityManifest]:
        return self.manifests

    def list_capabilities(self) -> list[dict[str, object]]:
        return [{"capability_id": "aion.internal.noop"}]


class FakeGateway:
    """Runtime gateway fake."""

    def __init__(self) -> None:
        self.runtimes = [runtime()]
        self.invocations: list[CapabilityInvocationRequest] = []

    def register_runtime(
        self,
        request: ModuleRuntimeRegistrationRequest,
    ) -> ModuleRuntimeRegistrationResponse:
        self.runtimes.append(request.runtime)
        return ModuleRuntimeRegistrationResponse(
            registered=True,
            runtime_id=request.runtime.runtime_id,
            module_id=request.runtime.module_id,
            version=request.runtime.version,
            binding_count=len(request.bind_capabilities),
            status="active",
            reason=None,
        )

    def list_runtimes(self) -> list[ModuleRuntime]:
        return self.runtimes

    def get_runtime(self, runtime_id: str) -> ModuleRuntime | None:
        for item in self.runtimes:
            if item.runtime_id == runtime_id:
                return item
        return None

    def health_check(self, runtime_id: str) -> ModuleHealthCheck:
        return ModuleHealthCheck(
            health_check_id="health-1",
            runtime_id=runtime_id,
            module_id="test.module",
            status="healthy",
            latency_ms=0,
            details={},
            created_at=datetime.now(UTC),
        )

    def bind_capability(self, request: CapabilityBindingRequest) -> CapabilityRuntimeBinding:
        return CapabilityRuntimeBinding(
            binding_id="binding-1",
            capability_id=request.capability_id,
            module_id=request.module_id,
            runtime_id=request.runtime_id,
            invocation_mode=request.invocation_mode,
            status=request.status,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityInvocationResult:
        self.invocations.append(request)
        return CapabilityInvocationResult(
            invocation_id=request.invocation_id,
            capability_id=request.capability_id,
            runtime_id="runtime-1",
            status="dry_run" if request.mode == "dry_run" else "completed",
            output={"ok": True},
            error={},
            policy_decision_id="decision-1",
            latency_ms=0,
            created_at=datetime.now(UTC),
        )


def test_modules_runtime_apis_work() -> None:
    """Runtime registration, list, get, and health APIs work."""
    gateway = FakeGateway()
    app.dependency_overrides[get_capability_runtime_gateway] = lambda: gateway
    try:
        client = TestClient(app)
        registered = client.post("/brain/modules/runtimes/register", json=registration_payload())
        listed = client.get("/brain/modules/runtimes")
        fetched = client.get("/brain/modules/runtimes/runtime-1")
        health = client.post("/brain/modules/runtimes/runtime-1/health-check")
    finally:
        app.dependency_overrides.clear()

    assert registered.status_code == 200
    assert registered.json()["registered"] is True
    assert listed.status_code == 200
    assert fetched.status_code == 200
    assert health.json()["status"] == "healthy"


def test_capability_manifest_and_invocation_apis_work() -> None:
    """Capability registry and gateway-backed invocation APIs work."""
    service = FakeCapabilityService()
    gateway = FakeGateway()
    app.dependency_overrides[get_capability_service] = lambda: service
    app.dependency_overrides[get_capability_runtime_gateway] = lambda: gateway
    try:
        client = TestClient(app)
        register = client.post("/brain/capabilities/register", json=manifest_payload())
        list_caps = client.get("/brain/capabilities")
        bind = client.post(
            "/brain/capabilities/aion.internal.noop/bind-runtime",
            json=binding_payload(),
        )
        invoke = client.post("/brain/capabilities/invoke", json=invocation_payload())
        legacy = client.post(
            "/brain/capabilities/aion.internal.noop/invoke",
            json={"mode": "dry_run", "payload": {"x": 1}},
        )
    finally:
        app.dependency_overrides.clear()

    assert register.status_code == 200
    assert list_caps.json()[0]["capability_id"] == "aion.internal.noop"
    assert bind.status_code == 200
    assert invoke.json()["status"] == "dry_run"
    assert legacy.status_code == 200
    assert gateway.invocations[-1].capability_id == "aion.internal.noop"


def runtime() -> ModuleRuntime:
    """Create a runtime."""
    return ModuleRuntime(
        runtime_id="runtime-1",
        module_id="test.module",
        version="0.1.0",
        runtime_type="local_internal",
        endpoint_ref=None,
        status="active",
        health_status="healthy",
        config={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def registration_payload() -> dict[str, object]:
    """Create a runtime registration payload."""
    return {
        "runtime": {
            "runtime_id": "runtime-2",
            "module_id": "test.module",
            "version": "0.1.0",
            "runtime_type": "local_internal",
            "endpoint_ref": None,
            "status": "registered",
            "health_status": "unknown",
            "config": {},
            "created_at": None,
            "updated_at": None,
            "last_health_check_at": None,
        },
        "bind_capabilities": [],
        "activate": True,
    }


def manifest_payload() -> dict[str, object]:
    """Create a capability manifest payload."""
    return {
        "module_id": "test.module",
        "version": "0.1.0",
        "capabilities": [{"capability_id": "aion.internal.noop"}],
        "permissions_required": [],
        "memory_read_scopes": [],
        "memory_write_scopes": [],
        "events_subscribed": [],
        "events_published": [],
        "execution_mode": "sync",
    }


def binding_payload() -> dict[str, object]:
    """Create a capability binding payload."""
    return {
        "capability_id": "aion.internal.noop",
        "module_id": "test.module",
        "runtime_id": "runtime-1",
        "invocation_mode": "dry_run",
        "status": "active",
    }


def invocation_payload() -> dict[str, object]:
    """Create an invocation payload."""
    return {
        "invocation_id": "invocation-1",
        "trace_id": "trace-1",
        "execution_id": None,
        "step_run_id": None,
        "capability_id": "aion.internal.noop",
        "actor_id": None,
        "workspace_id": None,
        "mode": "dry_run",
        "payload": {},
        "approval_present": False,
        "metadata": {},
    }
