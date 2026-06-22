"""Bootstrap and setup doctor contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.bootstrap import (
    BootstrapProfile,
    BootstrapRunRequest,
    SeedBundle,
)
from aion_brain.contracts.setup_doctor import SetupFinding, SetupReport


def test_bootstrap_profile_rejects_production_and_domain_terms() -> None:
    with pytest.raises(ValidationError):
        BootstrapProfile(
            bootstrap_profile_id="profile-1",
            profile_key="local.prod",
            name="Production profile",
            description="Prepare production setup.",
            status="active",
            profile_type="generic",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        BootstrapProfile(
            bootstrap_profile_id="profile-2",
            profile_key="local.dev",
            name="Finance profile",
            description="Generic local setup.",
            status="active",
            profile_type="generic",
            owner_scope=["workspace:main"],
        )


def test_seed_bundle_requires_idempotent_local_steps() -> None:
    with pytest.raises(ValidationError):
        SeedBundle(
            seed_bundle_id="bundle-1",
            seed_bundle_key="core.defaults",
            name="Core Defaults",
            description="Local defaults.",
            status="active",
            bundle_type="core_defaults",
            owner_scope=["workspace:main"],
            seed_steps=[{"service_key": "kernel"}],
            idempotency_keys=[],
            dependencies=[],
        )
    with pytest.raises(ValidationError):
        SeedBundle(
            seed_bundle_id="bundle-2",
            seed_bundle_key="core.defaults",
            name="Core Defaults",
            description="Local defaults.",
            status="active",
            bundle_type="core_defaults",
            owner_scope=["workspace:main"],
            seed_steps=[
                {"service_key": "kernel", "idempotency_key": "core", "external_calls": True}
            ],
            idempotency_keys=["core"],
            dependencies=[],
        )


def test_bootstrap_run_rejects_external_provider_and_full_autonomy_flags() -> None:
    with pytest.raises(ValidationError):
        BootstrapRunRequest(
            owner_scope=["workspace:main"],
            metadata={"enable_external_providers": True},
        )
    with pytest.raises(ValidationError):
        BootstrapRunRequest(
            owner_scope=["workspace:main"],
            metadata={"enable_full_autonomy": True},
        )


def test_setup_report_critical_findings_force_local_ready_false() -> None:
    finding = SetupFinding(
        setup_finding_id="finding-1",
        finding_type="service_unavailable",
        category="health",
        severity="critical",
        status="open",
        title="Missing service",
        description="A local service is missing.",
        check_key="health",
        expected={"available": True},
        actual={"available": False},
        recommended_action="start_local_stack",
        owner_scope=["workspace:main"],
    )
    report = SetupReport(
        setup_report_id="report-1",
        status="failed",
        owner_scope=["workspace:main"],
        readiness_score=1.0,
        local_ready=True,
        health_ready=True,
        policy_ready=True,
        sdk_ready=True,
        cli_ready=True,
        golden_path_ready=True,
        release_smoke_ready=True,
        docker_ready=True,
        finding_count=1,
        critical_count=1,
        warning_count=0,
        findings=[finding.model_dump(mode="json")],
        created_at=datetime.now(UTC),
    )

    assert report.local_ready is False
