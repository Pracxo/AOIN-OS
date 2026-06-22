"""Release package API tests."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.release_package import get_release_packager
from aion_brain.contracts.release_package import (
    ReleaseHandoffReport,
    ReleasePackage,
    ReleasePackageManifest,
    ReleasePackageRequest,
    ReleasePackageValidation,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


def test_release_package_api_routes_work() -> None:
    fake = FakeReleasePackager()
    app.dependency_overrides[get_release_packager] = lambda: fake
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/release-package/create",
            json={"version": "0.1.0", "scope": ["workspace:main"]},
        )
        package_id = created.json()["release_package_id"]
        fetched = client.get(
            f"/brain/release-package/{package_id}",
            params={"scope": "workspace:main"},
        )
        listed = client.get("/brain/release-package", params={"scope": "workspace:main"})
        validation = client.post(
            f"/brain/release-package/{package_id}/validate",
            params={"scope": "workspace:main"},
        )
        handoff = client.get(
            f"/brain/release-package/{package_id}/handoff",
            params={"scope": "workspace:main"},
        )
    finally:
        app.dependency_overrides.clear()

    status_codes = [
        response.status_code for response in [created, fetched, listed, validation, handoff]
    ]
    assert status_codes == [
        200,
        200,
        200,
        200,
        200,
    ]
    assert fake.created_scope == ["workspace:main"]
    assert handoff.json()["status"] == "ready"


class FakeReleasePackager:
    """Release packager fake."""

    def __init__(self) -> None:
        self.package_record = _package()
        self.created_scope: list[str] = []

    def package(
        self,
        request: ReleasePackageRequest,
        *,
        app: object | None = None,
    ) -> ReleasePackage:
        self.created_scope = request.owner_scope
        return self.package_record

    def get(self, release_package_id: str, scope: list[str]) -> ReleasePackage | None:
        return self.package_record

    def list(
        self,
        scope: list[str],
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> list[ReleasePackage]:
        return [self.package_record]

    def validate_package(
        self,
        release_package_id: str,
        scope: list[str],
    ) -> ReleasePackageValidation:
        return self.package_record.validation

    def handoff(self, release_package_id: str, scope: list[str]) -> ReleaseHandoffReport:
        return self.package_record.handoff_report


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


def _package() -> ReleasePackage:
    validation = ReleasePackageValidation(
        status="passed",
        checks=[],
        failures=[],
        warnings=[],
        generated_at=datetime.now(UTC),
    )
    handoff = ReleaseHandoffReport(
        version="0.1.0",
        status="ready",
        summary="ready",
        included_reports={},
        local_verification_commands=["scripts/check.sh"],
        known_limits=["local-first only"],
        next_steps=[],
        generated_at=datetime.now(UTC),
    )
    return ReleasePackage(
        release_package_id="release-package-1",
        version="0.1.0",
        status="dry_run",
        package_name="aion-0.1.0-local-release",
        package_path="artifacts/releases/aion-0.1.0-local-release",
        manifest=ReleasePackageManifest(
            version="0.1.0",
            package_name="aion-0.1.0-local-release",
            created_at=datetime.now(UTC),
            included_artifacts=["manifest"],
            excluded_artifacts=[],
            file_count=0,
            total_size_bytes=0,
            root_checksum="abc",
            metadata={},
        ),
        files=[],
        checksums={},
        validation=validation,
        handoff_report=handoff,
        created_by="tester",
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
