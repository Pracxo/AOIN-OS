"""Shared fakes for release package tests."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.release_package.packager import ReleasePackager
from aion_brain.release_package.repository import ReleasePackageRepository
from tests.versioning_fakes import (
    AllowPolicy,
    FakeArtifactService,
    FakeCompatibilityService,
    FakeContractExportService,
    FakeManifestService,
    FakeMigrationService,
    FakeReleaseBaselineService,
    freeze_gate_run,
)

SCOPE = ["workspace:main"]


class FakeApp:
    """Minimal FastAPI-like app fake."""

    def openapi(self) -> dict[str, object]:
        return {"openapi": "3.1.0", "paths": {"/health": {}}}


class FakeFreezeGateService:
    """Freeze gate service fake."""

    def run(self, request: object, *, app: object | None = None) -> object:
        return freeze_gate_run()


class FakePolicyBundleService:
    """Policy bundle export fake."""

    def export_bundle(self) -> dict[str, object]:
        return {"status": "complete", "policy_count": 1}


def repository() -> ReleasePackageRepository:
    """Return an in-memory release package repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ReleasePackageRepository(engine=engine)


def settings() -> Settings:
    """Return local test settings."""
    return Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")


def write_release_tree(root: Path) -> None:
    """Create a minimal generic release tree."""
    for relative, text in {
        "README.md": "AION generic release artifact.\n",
        "AGENTS.md": "AION agent operating guide.\n",
        "CHANGELOG.md": "# Changelog\n\n## 0.1.0\n- Generic Brain release.\n",
        "docs/release-notes/v0.1.0.md": "# AION v0.1.0\n",
        "docs/architecture.md": "AION Brain architecture.\n",
        "scripts/check.sh": "#!/usr/bin/env bash\nexit 0\n",
        "docker-compose.yml": "services: {}\n",
        "services/brain-api/src/aion_brain/__init__.py": "",
        "services/brain-api/pyproject.toml": (
            "[project]\nname = \"aion-brain-api\"\nversion = \"0.1.0\"\n"
            "dependencies = [\"fastapi\"]\n"
        ),
        "packages/aion-sdk-python/src/aion_sdk/__init__.py": "",
        "packages/aion-sdk-python/pyproject.toml": (
            "[project]\nname = \"aion-sdk-python\"\nversion = \"0.1.0\"\n"
            "dependencies = [\"httpx\"]\n"
        ),
        "infra/postgres/migrations/0001.py": "# migration\n",
        "infra/opa/policies/brain.rego": "package aion.brain\n",
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def packager(root: Path, policy: object | None = None) -> ReleasePackager:
    """Return a release packager with local fakes."""
    return ReleasePackager(
        repository(),
        policy or AllowPolicy(),  # type: ignore[arg-type]
        version_manifest_service=FakeManifestService(),
        contract_export_service=FakeContractExportService(),
        policy_bundle_service=FakePolicyBundleService(),
        migration_baseline_service=FakeMigrationService(),
        release_baseline_service=FakeReleaseBaselineService(),
        freeze_gate_service=FakeFreezeGateService(),
        compatibility_matrix_service=FakeCompatibilityService(),
        release_artifact_service=FakeArtifactService(),
        root_dir=root,
        settings=settings(),
    )
