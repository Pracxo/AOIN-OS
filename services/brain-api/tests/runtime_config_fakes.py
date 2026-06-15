"""Shared fakes for runtime configuration tests."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.runtime_config.feature_flags import FeatureFlagOverrideService
from aion_brain.runtime_config.profiles import ConfigProfileService
from aion_brain.runtime_config.repository import RuntimeConfigRepository
from aion_brain.runtime_config.snapshots import ConfigSnapshotService
from aion_brain.runtime_config.status import RuntimeConfigStatusService
from aion_brain.runtime_config.validator import ConfigValidator

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


class DenyPolicy(AllowPolicy):
    """Always deny policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=[],
            audit_level="standard",
        )


class FakeTelemetry:
    """Collect emitted telemetry."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


@dataclass
class FakeFeature:
    """Small feature entry shape for tests."""

    feature_key: str
    default_enabled: bool


class FakeFeatureRegistry:
    """Return stable test feature flags."""

    def list_features(self, scope: list[str]) -> list[FakeFeature]:
        return [
            FakeFeature("kernel.container", True),
            FakeFeature("runtime_config.feature_overrides", True),
        ]


def repository() -> RuntimeConfigRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return RuntimeConfigRepository(engine=engine)


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
    policy: AllowPolicy | None = None,
    configured_settings: Settings | None = None,
) -> tuple[
    RuntimeConfigRepository,
    ConfigProfileService,
    FeatureFlagOverrideService,
    ConfigSnapshotService,
    ConfigValidator,
    RuntimeConfigStatusService,
    FakeTelemetry,
]:
    repo = repository()
    selected_policy = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    local_settings = configured_settings or settings()
    feature_overrides = FeatureFlagOverrideService(
        repo,
        selected_policy,
        feature_registry=FakeFeatureRegistry(),
        telemetry_service=telemetry,
    )
    profiles = ConfigProfileService(repo, selected_policy, telemetry_service=telemetry)
    snapshots = ConfigSnapshotService(
        repo,
        selected_policy,
        feature_override_service=feature_overrides,
        settings=local_settings,
        telemetry_service=telemetry,
    )
    validator = ConfigValidator(
        repo,
        selected_policy,
        feature_override_service=feature_overrides,
        settings=local_settings,
        telemetry_service=telemetry,
    )
    status = RuntimeConfigStatusService(
        repo,
        selected_policy,
        feature_override_service=feature_overrides,
        telemetry_service=telemetry,
    )
    return repo, profiles, feature_overrides, snapshots, validator, status, telemetry
