"""Shared fakes for sandbox, secret reference, and connector tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.connectors.repository import ConnectorRepository
from aion_brain.connectors.service import ConnectorService
from aion_brain.contracts.connectors import ConnectorCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.sandbox import (
    ResourceLimits,
    RuntimePermission,
    RuntimePermissionGrantRequest,
    SandboxProfile,
    SandboxProfileCreateRequest,
)
from aion_brain.contracts.secrets import SecretRefCreateRequest
from aion_brain.sandbox.local_noop_adapter import LocalNoopSandboxAdapter
from aion_brain.sandbox.repository import SandboxRepository
from aion_brain.sandbox.service import SandboxService
from aion_brain.sandbox.validator import SandboxValidator
from aion_brain.secrets.repository import SecretRefRepository
from aion_brain.secrets.service import SecretRefService


class FakePolicyAdapter:
    """Policy fake that records requests."""

    def __init__(self, *, allow: bool = True, approval_required: bool = False) -> None:
        self.allow = allow
        self.approval_required = approval_required
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"policy-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=self.approval_required,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard",
        )


class FakeTelemetry:
    """Telemetry fake."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeRiskEngine:
    """Risk fake."""

    def __init__(self, decision: str = "allow") -> None:
        self.decision = decision

    def assess(self, request: object) -> object:
        return SimpleNamespace(risk_assessment_id="risk-1", decision=self.decision)


class FakeAutonomyGovernor:
    """Autonomy fake."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow

    def decide(self, request: object) -> object:
        return SimpleNamespace(
            autonomy_decision_id="autonomy-1",
            allow=self.allow,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
        )


def sqlite_engine() -> Engine:
    """Return a shared in-memory SQLite engine."""
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def settings(**overrides: Any) -> Settings:
    """Return test settings."""
    defaults: dict[str, Any] = {
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "AION_SANDBOX_EXECUTION_ENABLED": False,
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def resource_limits(**overrides: Any) -> ResourceLimits:
    """Return conservative resource limits."""
    payload = {
        "cpu_millis": 500,
        "memory_mb": 128,
        "timeout_seconds": 5,
        "max_output_bytes": 2048,
        "max_files": 10,
        "max_file_bytes": 1024,
    }
    payload.update(overrides)
    return ResourceLimits(**payload)


def runtime_permission(permission: str = "runtime.execute") -> RuntimePermission:
    """Return one runtime permission."""
    return RuntimePermission(permission=permission, allowed=True, reason="test")


def profile_request(**overrides: Any) -> SandboxProfileCreateRequest:
    """Return a sandbox profile create request."""
    payload = {
        "sandbox_profile_id": "sandbox-profile-1",
        "name": "Generic profile",
        "description": "Metadata-only local no-op profile",
        "sandbox_type": "local_noop",
        "owner_scope": ["workspace:main"],
        "resource_limits": resource_limits(),
        "egress_rules": [],
        "filesystem_rules": [],
        "allowed_runtime_permissions": [runtime_permission()],
        "secret_refs_allowed": [],
        "connector_refs_allowed": [],
        "network_enabled": False,
        "filesystem_write_enabled": False,
        "process_spawn_enabled": False,
        "metadata": {},
        "created_by": "dev",
        "activate": True,
    }
    payload.update(overrides)
    return SandboxProfileCreateRequest(**payload)


def profile(**overrides: Any) -> SandboxProfile:
    """Return a persisted-style profile."""
    request = profile_request(**overrides)
    return SandboxProfile(
        sandbox_profile_id=request.sandbox_profile_id or "sandbox-profile-1",
        name=request.name,
        description=request.description,
        status="active" if request.activate else "disabled",
        sandbox_type=request.sandbox_type,
        owner_scope=request.owner_scope,
        resource_limits=request.resource_limits,
        egress_rules=request.egress_rules,
        filesystem_rules=request.filesystem_rules,
        allowed_runtime_permissions=request.allowed_runtime_permissions,
        secret_refs_allowed=request.secret_refs_allowed,
        connector_refs_allowed=request.connector_refs_allowed,
        network_enabled=request.network_enabled,
        filesystem_write_enabled=request.filesystem_write_enabled,
        process_spawn_enabled=request.process_spawn_enabled,
        metadata=request.metadata,
        created_by=request.created_by,
    )


def secret_request(**overrides: Any) -> SecretRefCreateRequest:
    """Return a secret ref create request."""
    payload = {
        "secret_ref_id": "secret-ref-1",
        "name": "Generic external reference",
        "description": "Reference only",
        "owner_scope": ["workspace:main"],
        "secret_type": "api_key_ref",
        "provider": "metadata_only",
        "external_ref": "env:AION_GENERIC_REF",
        "sensitivity": "confidential",
        "rotation_policy": {"rotation": "manual"},
        "metadata": {"purpose": "generic"},
        "created_by": "dev",
    }
    payload.update(overrides)
    return SecretRefCreateRequest(**payload)


def connector_request(**overrides: Any) -> ConnectorCreateRequest:
    """Return a connector create request."""
    payload = {
        "connector_id": "connector-1",
        "name": "Generic connector",
        "description": "Metadata-only connector",
        "connector_type": "generic_placeholder",
        "owner_scope": ["workspace:main"],
        "base_endpoint_ref": "connector:endpoint:generic",
        "auth_secret_ref_id": None,
        "allowed_actions": ["read"],
        "allowed_scopes": ["workspace:main"],
        "risk_level": "medium",
        "metadata": {"purpose": "generic"},
        "created_by": "dev",
    }
    payload.update(overrides)
    return ConnectorCreateRequest(**payload)


def runtime_permission_request(**overrides: Any) -> RuntimePermissionGrantRequest:
    """Return a runtime permission grant request."""
    payload = {
        "runtime_permission_id": "runtime-permission-1",
        "target_type": "capability",
        "target_id": "test.echo",
        "sandbox_profile_id": "sandbox-profile-1",
        "owner_scope": ["workspace:main"],
        "permissions": [runtime_permission()],
        "secret_refs": [],
        "connector_refs": [],
        "granted_by": "dev",
        "metadata": {},
    }
    payload.update(overrides)
    return RuntimePermissionGrantRequest(**payload)


def make_sandbox_service(
    *,
    policy: FakePolicyAdapter | None = None,
    telemetry: FakeTelemetry | None = None,
    test_settings: Settings | None = None,
) -> SandboxService:
    """Create a sandbox service with in-memory persistence."""
    active_settings = test_settings or settings()
    return SandboxService(
        sandbox_repository=SandboxRepository(engine=sqlite_engine()),
        sandbox_validator=SandboxValidator(active_settings),
        risk_engine=FakeRiskEngine(),
        approval_service=None,
        autonomy_governor=FakeAutonomyGovernor(),
        policy_adapter=policy or FakePolicyAdapter(),
        telemetry_service=telemetry,
        settings=active_settings,
        adapters={"local_noop": LocalNoopSandboxAdapter(active_settings)},
    )


def make_secret_service(
    *,
    policy: FakePolicyAdapter | None = None,
    telemetry: FakeTelemetry | None = None,
) -> SecretRefService:
    """Create a secret ref service with in-memory persistence."""
    return SecretRefService(
        repository=SecretRefRepository(engine=sqlite_engine()),
        policy_adapter=policy or FakePolicyAdapter(),
        telemetry_service=telemetry,
    )


def make_connector_service(
    *,
    policy: FakePolicyAdapter | None = None,
    secret_service: SecretRefService | None = None,
    telemetry: FakeTelemetry | None = None,
) -> ConnectorService:
    """Create a connector service with in-memory persistence."""
    return ConnectorService(
        repository=ConnectorRepository(engine=sqlite_engine()),
        policy_adapter=policy or FakePolicyAdapter(),
        secret_ref_service=secret_service or make_secret_service(policy=policy),
        telemetry_service=telemetry,
    )
