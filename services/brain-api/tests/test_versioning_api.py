"""Versioning API tests."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.versioning import (
    get_compatibility_matrix_service,
    get_feature_registry_service,
    get_migration_baseline_service,
    get_release_artifact_service,
    get_sdk_compatibility_service,
    get_version_manifest_service,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.versioning import FeatureRegistryEntry
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from tests.versioning_fakes import (
    FakeArtifactService,
    FakeCompatibilityService,
    FakeManifestService,
    FakeMigrationService,
    FakeSDKCompatibilityService,
)


class FakeFeatureService:
    """Feature service fake."""

    def seed_defaults(self, scope: list[str], *, dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run, "feature_keys": ["kernel.container"], "feature_count": 1}

    def list_features(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> list[FeatureRegistryEntry]:
        return [_feature(scope)]

    def create_feature(self, entry: FeatureRegistryEntry) -> FeatureRegistryEntry:
        return entry

    def deprecate_feature(
        self,
        feature_key: str,
        scope: list[str],
        *,
        actor_id: str | None,
        reason: str,
    ) -> FeatureRegistryEntry:
        return _feature(scope).model_copy(update={"status": "deprecated"})


def test_versioning_api_routes_work() -> None:
    app.dependency_overrides[get_version_manifest_service] = lambda: FakeManifestService()
    app.dependency_overrides[get_feature_registry_service] = lambda: FakeFeatureService()
    app.dependency_overrides[get_compatibility_matrix_service] = lambda: FakeCompatibilityService()
    app.dependency_overrides[get_migration_baseline_service] = lambda: FakeMigrationService()
    app.dependency_overrides[get_release_artifact_service] = lambda: FakeArtifactService()
    app.dependency_overrides[get_sdk_compatibility_service] = lambda: FakeSDKCompatibilityService()
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        create_manifest = client.post(
            "/brain/versioning/manifests",
            json={"version": "0.1.0", "scope": ["workspace:main"]},
        )
        get_manifest = client.get("/brain/versioning/manifests/0.1.0")
        list_manifests = client.get("/brain/versioning/manifests")
        freeze_manifest = client.post(
            "/brain/versioning/manifests/0.1.0/freeze",
            json={"scope": ["workspace:main"], "reason": "ready"},
        )
        seed_features = client.post(
            "/brain/versioning/features/seed-defaults",
            json={"scope": ["workspace:main"], "dry_run": True},
        )
        features = client.get("/brain/versioning/features", params={"scope": "workspace:main"})
        compatibility = client.post(
            "/brain/versioning/compatibility/generate",
            json={"version": "0.1.0", "scope": ["workspace:main"]},
        )
        migration = client.post(
            "/brain/versioning/migration-baseline/generate",
            json={"schema_version": "0.1.0", "scope": ["workspace:main"]},
        )
        artifacts = client.post(
            "/brain/versioning/release-artifacts/generate",
            json={"version": "0.1.0", "scope": ["workspace:main"]},
        )
        sdk = client.get("/brain/versioning/sdk-compatibility", params={"scope": "workspace:main"})
    finally:
        app.dependency_overrides.clear()

    responses = [
        create_manifest,
        get_manifest,
        list_manifests,
        freeze_manifest,
        seed_features,
        features,
        compatibility,
        migration,
        artifacts,
        sdk,
    ]
    assert all(response.status_code == 200 for response in responses)
    assert create_manifest.json()["version"] == "0.1.0"
    assert seed_features.json()["feature_count"] == 1


def actor_context() -> ActorContext:
    """Return dev actor context."""
    return ActorContext(
        actor_id="tester",
        actor_type="developer",
        workspace_id="main",
        roles=["owner"],
        permissions=["*"],
        security_scope=["workspace:main"],
        dev_mode=True,
    )


def _feature(scope: list[str]) -> FeatureRegistryEntry:
    return FeatureRegistryEntry(
        feature_id="feature-kernel-container",
        feature_key="kernel.container",
        name="Kernel Container",
        description="Generic kernel composition.",
        status="active",
        category="kernel",
        default_enabled=True,
        required=True,
        owner_scope=scope,
        dependencies=[],
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
