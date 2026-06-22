"""Shared fakes for security baseline tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.security_baseline.adapter_risk import AdapterRiskChecker
from aion_brain.security_baseline.api_exposure import APIExposureChecker
from aion_brain.security_baseline.config_checker import ConfigHardeningChecker
from aion_brain.security_baseline.control_catalog import SecurityControlCatalog
from aion_brain.security_baseline.dependency_metadata import DependencyMetadataScanner
from aion_brain.security_baseline.hardening_gate import HardeningGateService
from aion_brain.security_baseline.repository import SecurityBaselineRepository
from aion_brain.security_baseline.secret_scanner import SecretScanner
from aion_brain.security_baseline.threat_model import ThreatModelService

SCOPE = ["workspace:main"]


class AllowPolicy:
    """Always allow policy fake."""

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


class FakeTelemetry:
    """Collect emitted telemetry."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> SecurityBaselineRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return SecurityBaselineRepository(engine=engine)


def settings(**overrides: object) -> Settings:
    payload = {
        "_env_file": None,
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "AION_DEFAULT_SEMANTIC_ADAPTER": "in_memory",
        "AION_GRAPH_MEMORY_ADAPTER": "in_memory",
    }
    payload.update(overrides)
    return Settings(**payload)  # type: ignore[arg-type]


def services(
    *,
    root_dir: object | None = None,
    configured_settings: Settings | None = None,
) -> tuple[
    SecurityBaselineRepository,
    SecretScanner,
    ThreatModelService,
    SecurityControlCatalog,
    HardeningGateService,
    FakeTelemetry,
]:
    repo = repository()
    policy = AllowPolicy()
    telemetry = FakeTelemetry()
    local_settings = configured_settings or settings()
    scanner = SecretScanner(
        repo,
        policy,
        settings=local_settings,
        telemetry_service=telemetry,
        root_dir=root_dir,  # type: ignore[arg-type]
    )
    threat_model = ThreatModelService(repo, policy, telemetry_service=telemetry)
    controls = SecurityControlCatalog(repo, policy, telemetry_service=telemetry)
    hardening = HardeningGateService(
        repo,
        policy,
        secret_scanner=scanner,
        config_checker=ConfigHardeningChecker(local_settings, root_dir=root_dir),  # type: ignore[arg-type]
        api_exposure_checker=APIExposureChecker(),
        adapter_risk_checker=AdapterRiskChecker(local_settings, root_dir=root_dir),  # type: ignore[arg-type]
        dependency_metadata_scanner=DependencyMetadataScanner(root_dir=root_dir),  # type: ignore[arg-type]
        threat_model_service=threat_model,
        security_control_catalog=controls,
        telemetry_service=telemetry,
        settings=local_settings,
    )
    return repo, scanner, threat_model, controls, hardening, telemetry
