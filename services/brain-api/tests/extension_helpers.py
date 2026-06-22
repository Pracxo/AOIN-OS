"""Shared helpers for Extension Registry tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.extensions import ExtensionIntakeRequest, ExtensionManifest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.extensions.capabilities import CapabilityDeclarationService
from aion_brain.extensions.compatibility_gate import ExtensionCompatibilityGate
from aion_brain.extensions.dependencies import DependencyDeclarationService
from aion_brain.extensions.install_plans import InstallPlanService
from aion_brain.extensions.intake import ExtensionIntakeService
from aion_brain.extensions.manifest_validator import ManifestValidator
from aion_brain.extensions.packages import ExtensionPackageService
from aion_brain.extensions.query import ExtensionQueryService
from aion_brain.extensions.repository import ExtensionRegistryRepository
from aion_brain.extensions.reviews import ExtensionReviewService
from tests.kernel_fakes import AllowPolicy, FakeTelemetry


class DenyPolicy:
    """Always-deny local policy fake."""

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


def extension_manifest(**overrides: object) -> ExtensionManifest:
    payload = {
        "extension_key": "test.echo",
        "name": "Echo Extension",
        "description": "Generic metadata extension.",
        "version": "0.1.0",
        "package_type": "module",
        "declared_capabilities": [
            {
                "capability_key": "test.echo.respond",
                "capability_type": "generic",
                "risk_level": "low",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
        ],
        "declared_contracts": [],
        "declared_dependencies": [
            {
                "dependency_key": "extension.query",
                "dependency_type": "aion_policy_action",
                "required": True,
            }
        ],
        "declared_policy_actions": ["extension.query"],
        "declared_settings": [],
        "declared_routes": [],
        "declared_events": ["test.event"],
        "declared_resources": ["generic"],
        "sandbox_requirements": {},
        "permissions": [],
        "metadata": {"fixture": True},
    }
    payload.update(overrides)
    return ExtensionManifest.model_validate(payload)


def extension_intake_request(**overrides: object) -> ExtensionIntakeRequest:
    payload = {
        "mode": "dry_run",
        "owner_scope": ["workspace:main"],
        "manifest": extension_manifest(),
        "metadata": {"fixture": True},
    }
    payload.update(overrides)
    return ExtensionIntakeRequest.model_validate(payload)


def extension_repository() -> ExtensionRegistryRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ExtensionRegistryRepository(engine=engine)


def extension_services(
    policy: object | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    repository = extension_repository()
    policy_adapter = policy or AllowPolicy()
    resolved_settings = settings or Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
    )
    telemetry = FakeTelemetry()
    validator = ManifestValidator(resolved_settings)
    package_service = ExtensionPackageService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
        settings=resolved_settings,
    )
    dependency_service = DependencyDeclarationService(
        repository,
        policy_adapter,
        settings=resolved_settings,
    )
    capability_service = CapabilityDeclarationService(repository, policy_adapter)
    compatibility_gate = ExtensionCompatibilityGate(
        repository,
        policy_adapter,
        manifest_validator=validator,
        dependency_service=dependency_service,
        capability_service=capability_service,
        telemetry_service=telemetry,
        settings=resolved_settings,
    )
    install_plan_service = InstallPlanService(
        repository,
        policy_adapter,
        telemetry_service=telemetry,
        settings=resolved_settings,
    )
    intake_service = ExtensionIntakeService(
        repository,
        policy_adapter,
        manifest_validator=validator,
        package_service=package_service,
        dependency_service=dependency_service,
        capability_service=capability_service,
        compatibility_gate=compatibility_gate,
        install_plan_service=install_plan_service,
        telemetry_service=telemetry,
        settings=resolved_settings,
    )
    return {
        "repository": repository,
        "settings": resolved_settings,
        "telemetry": telemetry,
        "manifest_validator": validator,
        "package_service": package_service,
        "dependency_service": dependency_service,
        "capability_service": capability_service,
        "compatibility_gate": compatibility_gate,
        "install_plan_service": install_plan_service,
        "intake_service": intake_service,
        "query_service": ExtensionQueryService(repository, policy_adapter),
        "review_service": ExtensionReviewService(repository, policy_adapter),
    }
