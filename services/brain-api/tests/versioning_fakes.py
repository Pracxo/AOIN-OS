"""Shared fakes for versioning and freeze-gate tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.compatibility import (
    CompatibilityMatrix,
    MigrationBaseline,
    ReleaseArtifactManifest,
    SDKCompatibilityReport,
)
from aion_brain.contracts.freeze import FreezeGateCheck, FreezeGateRun
from aion_brain.contracts.kernel import KernelSelfTestResult
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.versioning.repository import VersioningRepository

SCOPE = ["workspace:main"]


class AllowPolicy:
    """Always-allow policy fake."""

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


class DenyPolicy:
    """Always-deny policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=[],
            audit_level="high",
        )


class FakeTelemetry:
    """Collect emitted telemetry."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> VersioningRepository:
    """Return an in-memory versioning repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return VersioningRepository(engine=engine)


def settings() -> Settings:
    """Return local test settings."""
    return Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")


class FakeManifestService:
    """Minimal manifest service fake."""

    def create_manifest(
        self,
        version: str,
        created_by: str | None,
        owner_scope: list[str],
        *,
        app: object | None = None,
    ) -> object:
        from aion_brain.contracts.versioning import VersionManifest

        return VersionManifest(
            version_manifest_id="manifest-1",
            version=version,
            release_channel="alpha",
            status="active",
            api_version="v1",
            sdk_version="0.1.0",
            schema_version=version,
            contract_hash="abc",
            feature_flags={"kernel.container": True},
            adapter_matrix={"required": {"postgres": True}},
            metadata={"owner_scope": owner_scope, "created_by": created_by},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )

    def get_manifest(self, version: str, scope: list[str]) -> object:
        return self.create_manifest(version, "test", scope)

    def list_manifests(self, scope: list[str], *, status: str | None = None) -> list[object]:
        return [self.create_manifest("0.1.0", "test", scope)]

    def freeze_manifest(
        self,
        version: str,
        actor_id: str | None,
        reason: str,
        scope: list[str],
    ) -> object:
        manifest = self.create_manifest(version, actor_id, scope)
        return manifest.model_copy(update={"status": "frozen", "metadata": {"reason": reason}})


class FakeCompatibilityService:
    """Compatibility service fake."""

    def generate(self, version: str, scope: list[str]) -> CompatibilityMatrix:
        return _compatibility(version)

    def get(self, version: str, scope: list[str]) -> CompatibilityMatrix:
        return _compatibility(version)


class FakeMigrationService:
    """Migration baseline service fake."""

    def generate(self, schema_version: str, scope: list[str]) -> MigrationBaseline:
        return MigrationBaseline(
            migration_baseline_id="migration-1",
            schema_version=schema_version,
            migration_count=1,
            migration_hash="hash",
            destructive_migrations=[],
            tables=["aion_events"],
            status="passed",
            report={},
            created_at=datetime.now(UTC),
        )


class FakeArtifactService:
    """Release artifact service fake."""

    def generate(
        self,
        version: str,
        created_by: str | None,
        scope: list[str],
    ) -> ReleaseArtifactManifest:
        return ReleaseArtifactManifest(
            release_artifact_id="artifact-1",
            version=version,
            status="complete",
            artifacts={"files": []},
            checksums={},
            report={},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )


class FakeSDKCompatibilityService:
    """SDK compatibility fake."""

    def check(self, scope: list[str]) -> SDKCompatibilityReport:
        return SDKCompatibilityReport(
            report_id="sdk-1",
            api_version="v1",
            sdk_version="0.1.0",
            compatible=True,
            checked_endpoints=["/health"],
            missing_endpoints=[],
            mismatched_contracts=[],
            warnings=[],
            generated_at=datetime.now(UTC),
        )


class FakeReleaseBaselineService:
    """Release baseline service fake."""

    def run(self, request: object) -> object:
        return type(
            "ReleaseBaseline",
            (),
            {"status": "passed", "release_baseline_id": "baseline-1"},
        )()


class FakeKernelSelfTest:
    """Kernel self-test fake."""

    def run(self, request: object) -> KernelSelfTestResult:
        return KernelSelfTestResult(
            self_test_id=f"self-test-{uuid4().hex}",
            status="passed",
            checks=[],
            report={},
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )


class FakeSimpleCheckService:
    """Generic service with a passed check/generate method."""

    def check(self, *args: Any, **kwargs: Any) -> object:
        return type("Report", (), {"status": "passed", "violations": []})()

    def generate(self, *args: Any, **kwargs: Any) -> object:
        return type("Report", (), {"status": "passed"})()


class FakeContractExportService:
    """Contract export fake."""

    def export_contracts(self, app: object) -> object:
        class Export:
            contracts = {"AIONEvent": {}}

            def model_dump(self, mode: str = "json") -> dict[str, object]:
                return {"contracts": {"AIONEvent": {}}}

        return Export()


def freeze_gate_run(status: str = "passed") -> FreezeGateRun:
    """Return a persisted freeze gate run."""
    check = FreezeGateCheck(
        check_id="check-1",
        name="unit",
        category="test",
        status="passed",
        severity="low",
        message="ok",
        details={},
    )
    return FreezeGateRun(
        freeze_gate_id="freeze-1",
        version="0.1.0",
        status=status,  # type: ignore[arg-type]
        requested_by="tester",
        checks=[check],
        failures=[] if status == "passed" else [{"name": "unit"}],
        warnings=[],
        report={},
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def write_minimal_release_docs(root: Path) -> None:
    """Create minimal release docs for freeze/artifact tests."""
    for relative in [
        "README.md",
        "AGENTS.md",
        "CHANGELOG.md",
        "docs/versioning.md",
        "docs/upgrade-policy.md",
        "docs/deprecation-policy.md",
        "docs/release-notes/v0.1.0.md",
        "docker-compose.yml",
        "packages/aion-sdk-python/pyproject.toml",
        "docs/adr/0036-version-manifest-compatibility-freeze-gate.md",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("AION generic release artifact.\n", encoding="utf-8")
    (root / "docs/adr/README.md").write_text(
        "0036-version-manifest-compatibility-freeze-gate\n",
        encoding="utf-8",
    )
    (root / "infra/postgres/migrations").mkdir(parents=True, exist_ok=True)
    (root / "infra/postgres/migrations/0001.py").write_text(
        "def upgrade():\n    op.create_table('aion_events')\n\ndef downgrade():\n    pass\n",
        encoding="utf-8",
    )
    (root / "infra/opa/policies").mkdir(parents=True, exist_ok=True)
    (root / "infra/opa/policies/brain.rego").write_text("package aion.brain\n", encoding="utf-8")
    (root / "services/brain-api").mkdir(parents=True, exist_ok=True)


def _compatibility(version: str) -> CompatibilityMatrix:
    return CompatibilityMatrix(
        compatibility_matrix_id="compatibility-1",
        version=version,
        api_version="v1",
        sdk_version="0.1.0",
        python_version="3.12.0",
        optional_adapters={"turbovec": {"required": False, "available": False}},
        compatibility={"external_calls": False},
        status="warning",
        created_at=datetime.now(UTC),
    )
