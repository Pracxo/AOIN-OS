"""Shared helpers for model provider hardening tests."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.model_provider_hardening import (
    ModelProviderReadinessRequest,
    ModelProviderSimulationRequest,
    PromptEgressPreviewRequest,
)
from aion_brain.model_provider_hardening import (
    ModelProviderBlockerService,
    ModelProviderHardeningRepository,
    ModelProviderProfileService,
    ModelProviderReadinessService,
    ModelProviderSimulator,
    PromptEgressGuard,
    ProviderHardeningQueryService,
)
from tests.kernel_fakes import AllowPolicy, FakeTelemetry

SCOPE = ["workspace:main"]


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
        assert metadata["model_invoked"] is False
        self.records.append((record_type, record_id))


def settings(**overrides: object) -> Settings:
    """Return local-only safe settings."""

    payload: dict[str, object] = {
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        **overrides,
    }
    return Settings(_env_file=None, **payload)


def repository() -> ModelProviderHardeningRepository:
    """Return an in-memory repository safe for TestClient thread use."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ModelProviderHardeningRepository(engine=engine)


def services(policy: object | None = None, **setting_overrides: object) -> dict[str, object]:
    """Return provider hardening services with local fakes."""

    repo = repository()
    policy_adapter = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    local_settings = settings(**setting_overrides)
    return {
        "repository": repo,
        "settings": local_settings,
        "telemetry": telemetry,
        "profile_service": ModelProviderProfileService(
            repo,
            policy_adapter,
            telemetry_service=telemetry,
            settings=local_settings,
        ),
        "egress_guard": PromptEgressGuard(
            repo,
            policy_adapter,
            telemetry_service=telemetry,
            settings=local_settings,
        ),
        "simulator": ModelProviderSimulator(
            repo,
            policy_adapter,
            telemetry_service=telemetry,
            provenance_service=FakeProvenance(),
            settings=local_settings,
        ),
        "readiness_service": ModelProviderReadinessService(
            repo,
            policy_adapter,
            telemetry_service=telemetry,
            settings=local_settings,
        ),
        "blocker_service": ModelProviderBlockerService(
            repo,
            policy_adapter,
            telemetry_service=telemetry,
        ),
        "query_service": ProviderHardeningQueryService(repo, policy_adapter),
    }


def egress_request(**overrides: object) -> PromptEgressPreviewRequest:
    """Return a valid egress preview request."""

    payload: dict[str, object] = {
        "provider_key": "generic.metadata_only",
        "preview_type": "dry_run",
        "owner_scope": SCOPE,
        "prompt_summary": {"section_count": 1, "raw_prompt_included": False},
    }
    payload.update(overrides)
    return PromptEgressPreviewRequest.model_validate(payload)


def simulation_request(**overrides: object) -> ModelProviderSimulationRequest:
    """Return a valid provider simulation request."""

    payload: dict[str, object] = {
        "provider_key": "generic.metadata_only",
        "simulation_type": "dry_run",
        "owner_scope": SCOPE,
        "simulated_request": {"input_manifest_ref": "manifest-1"},
        "expected_response_shape": {"type": "object", "grounded": True},
    }
    payload.update(overrides)
    return ModelProviderSimulationRequest.model_validate(payload)


def readiness_request(**overrides: object) -> ModelProviderReadinessRequest:
    """Return a valid readiness request."""

    payload: dict[str, object] = {
        "provider_key": "generic.metadata_only",
        "owner_scope": SCOPE,
        "simulation_refs": ["simulation-1"],
    }
    payload.update(overrides)
    return ModelProviderReadinessRequest.model_validate(payload)
