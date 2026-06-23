"""Shared helpers for module mock runtime tests."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.module_mock_runtime import ModuleMockInvocationCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.module_mock_runtime import (
    ModuleMockFindingService,
    ModuleMockProfileService,
    ModuleMockQueryService,
    ModuleMockRuntimeRepository,
    ModuleMockSchemaAdapter,
    ModuleMockSimulator,
)
from tests.kernel_fakes import AllowPolicy, FakeTelemetry
from tests.module_binding_helpers import binding_request, module_binding_services, slot_request

SCOPE = ["workspace:main"]


class DenyPolicy:
    """Always deny module mock policy requests."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="test_denied",
            constraints=[],
            audit_level="standard",
        )


class FakeExternalService:
    """Raises if the mock runtime tries to call an external dependency."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"external service should not be called: {name}")


class FakeProvenance:
    """Collect provenance records."""

    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []

    def record(
        self,
        record_type: str,
        record_id: str,
        _scope: list[str],
        *,
        metadata: dict[str, Any],
    ) -> None:
        assert metadata["synthetic"] is True
        self.records.append((record_type, record_id))


def settings() -> Settings:
    """Return local-only safe settings."""

    return Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")


def repository() -> ModuleMockRuntimeRepository:
    """Return an in-memory repository safe for TestClient thread use."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ModuleMockRuntimeRepository(engine=engine)


def bound_module() -> tuple[dict[str, object], str, str]:
    """Create module slot and capability binding metadata."""

    services = module_binding_services(settings=settings())
    slot = services["slot_service"].create_slot(  # type: ignore[attr-defined]
        slot_request(declared_capability_refs=["generic.knowledge.answer"])
    )
    binding = services["binding_service"].create_binding(  # type: ignore[attr-defined]
        binding_request(
            slot.module_slot_id,
            capability_key="generic.knowledge.answer",
            route_key="generic.knowledge.answer",
            input_schema={"type": "object", "required": ["query"]},
            output_schema={"type": "object", "synthetic": True},
        )
    )
    return services, slot.module_slot_id, binding.capability_binding_id


def services(policy: object | None = None) -> dict[str, object]:
    """Return module mock services with local test dependencies."""

    repo = repository()
    policy_adapter = policy or AllowPolicy()
    binding_services, _slot_id, _binding_id = bound_module()
    telemetry = FakeTelemetry()
    adapter = ModuleMockSchemaAdapter()
    return {
        "repository": repo,
        "settings": settings(),
        "policy": policy_adapter,
        "binding_repository": binding_services["repository"],
        "telemetry": telemetry,
        "profile_service": ModuleMockProfileService(
            repo,
            policy_adapter,
            telemetry_service=telemetry,
            settings=settings(),
        ),
        "schema_adapter": adapter,
        "simulator": ModuleMockSimulator(
            repo,
            policy_adapter,
            module_binding_repository=binding_services["repository"],
            schema_adapter=adapter,
            telemetry_service=telemetry,
            settings=settings(),
        ),
        "finding_service": ModuleMockFindingService(repo, policy_adapter),
        "query_service": ModuleMockQueryService(repo, policy_adapter),
    }


def invocation_request(
    capability_binding_id: str,
    **overrides: object,
) -> ModuleMockInvocationCreateRequest:
    """Return a valid dry-run invocation request."""

    payload: dict[str, object] = {
        "capability_binding_id": capability_binding_id,
        "capability_key": "generic.knowledge.answer",
        "invocation_type": "mock_answer",
        "mode": "dry_run",
        "owner_scope": SCOPE,
        "input_payload": {"query": "generic test query"},
        "expected_output_shape": {"type": "object", "synthetic": True},
        "policy_refs": ["module_mock.invoke"],
        "sandbox_refs": ["sandbox.metadata_only"],
        "metadata": {"metadata_only": True},
    }
    payload.update(overrides)
    return ModuleMockInvocationCreateRequest.model_validate(payload)
