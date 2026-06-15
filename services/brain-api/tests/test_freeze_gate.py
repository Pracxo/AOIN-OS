"""Freeze gate service tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.freeze import FreezeGateRunRequest
from aion_brain.freeze.gate import FreezeGateService
from aion_brain.versioning.features import FeatureRegistryService
from aion_brain.versioning.migrations import MigrationBaselineService
from tests.versioning_fakes import (
    SCOPE,
    AllowPolicy,
    DenyPolicy,
    FakeArtifactService,
    FakeCompatibilityService,
    FakeContractExportService,
    FakeKernelSelfTest,
    FakeManifestService,
    FakeReleaseBaselineService,
    FakeSDKCompatibilityService,
    FakeSimpleCheckService,
    repository,
    settings,
    write_minimal_release_docs,
)


def test_freeze_gate_passes_with_local_fakes(tmp_path: Path) -> None:
    write_minimal_release_docs(tmp_path)
    service = _service(tmp_path)

    run = service.run(
        FreezeGateRunRequest(
            version="0.1.0",
            requested_by="tester",
            owner_scope=SCOPE,
        ),
        app=FakeApp(),
    )

    assert run.status in {"passed", "warning"}
    assert {check.name for check in run.checks} >= {
        "version_manifest_can_be_created",
        "migration_baseline",
        "release_artifact_manifest",
        "no_full_autonomy_default",
        "performance_baseline_available",
        "benchmark_smoke_passed",
    }


def test_freeze_gate_policy_deny_blocks_run(tmp_path: Path) -> None:
    service = _service(tmp_path, policy=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        service.run(FreezeGateRunRequest(version="0.1.0", owner_scope=SCOPE), app=FakeApp())


def test_freeze_gate_get_returns_persisted_run(tmp_path: Path) -> None:
    write_minimal_release_docs(tmp_path)
    service = _service(tmp_path)
    run = service.run(FreezeGateRunRequest(version="0.1.0", owner_scope=SCOPE), app=FakeApp())

    fetched = service.get(run.freeze_gate_id, SCOPE)

    assert fetched is not None
    assert fetched.freeze_gate_id == run.freeze_gate_id


class FakeApp:
    """Minimal FastAPI-like app fake."""

    def openapi(self) -> dict[str, object]:
        return {"openapi": "3.1.0", "paths": {"/health": {}}}


def _service(tmp_path: Path, policy: object | None = None) -> FreezeGateService:
    policy = policy or AllowPolicy()
    repo = repository()
    migrations = MigrationBaselineService(
        repo,
        policy,  # type: ignore[arg-type]
        migrations_dir=tmp_path / "infra/postgres/migrations",
    )
    features = FeatureRegistryService(repo, policy)  # type: ignore[arg-type]
    return FreezeGateService(
        repo,
        policy,  # type: ignore[arg-type]
        version_manifest_service=FakeManifestService(),
        feature_registry_service=features,
        compatibility_matrix_service=FakeCompatibilityService(),
        migration_baseline_service=migrations,
        release_artifact_service=FakeArtifactService(),
        sdk_compatibility_service=FakeSDKCompatibilityService(),
        release_baseline_service=FakeReleaseBaselineService(),
        kernel_self_test=FakeKernelSelfTest(),
        policy_coverage=FakeSimpleCheckService(),
        openapi_hygiene=FakeSimpleCheckService(),
        boundary_checker=FakeSimpleCheckService(),
        contract_export_service=FakeContractExportService(),
        root_dir=tmp_path,
        settings=settings(),
    )
