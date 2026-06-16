"""Shared module developer test helpers."""

from datetime import UTC, datetime
from typing import Any

from aion_brain.config import Settings
from aion_brain.contracts.autonomy import AutonomyDecision
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.module_developer import ModulePackage, ModulePackageCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessment
from aion_brain.module_developer.certifier import ModuleCertifier
from aion_brain.module_developer.repository import ModuleDeveloperRepository
from aion_brain.module_developer.validator import ModulePackageValidator


class AllowPolicy:
    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy(AllowPolicy):
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=["test"],
            audit_level="high",
        )


class FakeAutonomy:
    def decide(self, request: object) -> AutonomyDecision:
        return AutonomyDecision(
            autonomy_decision_id="autonomy-1",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            requested_mode="dry_run",
            resolved_mode="dry_run",
            action_type="capability.invoke",
            resource_type="capability",
            resource_id=None,
            risk_level="low",
            allow=True,
            approval_required=False,
            delegation_id=None,
            autonomy_profile_id=None,
            run_level_id=None,
            reason="allowed",
            constraints=[],
            metadata={},
            created_at=datetime.now(UTC),
        )


class FakeRisk:
    def assess(self, request: object) -> RiskAssessment:
        return RiskAssessment(
            risk_assessment_id="risk-1",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            action_type="capability.invoke",
            resource_type="capability",
            resource_id=None,
            requested_risk_level="low",
            computed_risk_level="low",
            risk_score=0.1,
            factors=[],
            constraints=[],
            decision="allow",
            metadata={},
            created_at=datetime.now(UTC),
        )


class FakeRuntimeGateway:
    def __init__(self) -> None:
        self.certified: list[str] = []
        self.invoked = False

    def certify_dry_run(self, capability_id: str) -> dict[str, Any]:
        self.certified.append(capability_id)
        return {
            "capability_id": capability_id,
            "module_code_executed": False,
            "external_calls": False,
        }

    def invoke(self, request: object) -> None:
        self.invoked = True


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def manifest(**overrides: object) -> CapabilityManifest:
    capability = {
        "capability_id": "generic.example.echo",
        "name": "generic.echo",
        "description": "Generic echo contract.",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "risk_level": "low",
        "permissions_required": ["capability.invoke"],
        "memory_read_scopes": [],
        "memory_write_scopes": [],
        "execution_mode": "sync",
        "timeout_seconds": 5,
        "audit_level": "full",
        "metadata": {},
    }
    data: dict[str, object] = {
        "module_id": "generic.example",
        "version": "0.1.0",
        "capabilities": [capability],
        "permissions_required": ["capability.invoke"],
        "memory_read_scopes": [],
        "memory_write_scopes": [],
        "events_subscribed": [],
        "events_published": [],
        "execution_mode": "sync",
    }
    data.update(overrides)
    return CapabilityManifest.model_validate(data)


def package_request(**overrides: object) -> ModulePackageCreateRequest:
    data: dict[str, object] = {
        "module_id": "generic.example",
        "version": "0.1.0",
        "package_name": "generic-example",
        "display_name": "Generic Example",
        "description": "Generic package.",
        "manifest": manifest(),
        "metadata": {},
    }
    data.update(overrides)
    return ModulePackageCreateRequest.model_validate(data)


def package(**overrides: object) -> ModulePackage:
    now = datetime.now(UTC)
    data: dict[str, object] = {
        "module_package_id": "pkg-1",
        "module_id": "generic.example",
        "version": "0.1.0",
        "package_name": "generic-example",
        "display_name": "Generic Example",
        "description": "Generic package.",
        "status": "submitted",
        "manifest": manifest(),
        "compatibility": {},
        "metadata": {},
        "created_by": "tester",
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return ModulePackage.model_validate(data)


def certifier(
    repository: ModuleDeveloperRepository,
    *,
    policy: AllowPolicy | None = None,
    runtime_gateway: FakeRuntimeGateway | None = None,
    telemetry: FakeTelemetry | None = None,
) -> ModuleCertifier:
    return ModuleCertifier(
        repository=repository,
        validator=ModulePackageValidator(),
        capability_service=object(),
        runtime_gateway=runtime_gateway or FakeRuntimeGateway(),
        policy_adapter=policy or AllowPolicy(),
        autonomy_governor=FakeAutonomy(),
        risk_engine=FakeRisk(),
        telemetry_service=telemetry,
        settings=Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"),
    )
