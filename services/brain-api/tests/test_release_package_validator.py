"""Release package validator tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.release_package import ReleasePackageFile, ReleasePackageRequest
from aion_brain.release_package.validator import ReleasePackageValidator


def test_release_package_validator_passes_generic_package() -> None:
    request = ReleasePackageRequest(version="0.1.0", owner_scope=["workspace:main"])
    files = [
        _file("README.md", "docs"),
        _file("AGENTS.md", "docs"),
        _file("CHANGELOG.md", "changelog"),
        _file("RELEASE_NOTES.md", "release_notes"),
        _file("generated/contract-export.json", "contract"),
        _file("generated/policy-bundle.json", "policy"),
        _file("generated/sbom.json", "sbom"),
    ]
    reports = {
        "contract_export": {},
        "freeze_gate": {},
        "release_baseline": {},
        "migration_baseline": {},
        "policy_bundle": {},
        "sbom": {},
        "no_domain_drift": {"status": "passed"},
        "autonomy_defaults": {"full_autonomy_enabled": False},
        "compatibility_matrix": {"optional_adapters": {"turbovec": {"required": False}}},
    }

    validation = ReleasePackageValidator().validate(request, files, reports)

    assert validation.status == "passed"
    assert not validation.failures


def test_release_package_validator_fails_env_and_cache_files() -> None:
    request = ReleasePackageRequest(version="0.1.0", owner_scope=["workspace:main"])
    files = [
        _file("README.md", "docs"),
        _file("AGENTS.md", "docs"),
        _file("CHANGELOG.md", "changelog"),
        _file("RELEASE_NOTES.md", "release_notes"),
        _file(".env", "config"),
        _file("services/brain-api/src/.pytest_cache/cache.py", "source"),
    ]

    validation = ReleasePackageValidator().validate(request, files, {})

    names = {failure["name"] for failure in validation.failures}
    assert validation.status == "failed"
    assert "no_env_included" in names
    assert "no_cache_dirs_included" in names


def _file(path: str, artifact_type: str) -> ReleasePackageFile:
    return ReleasePackageFile(
        release_package_file_id=f"file-{path.replace('/', '-')}",
        release_package_id="package-1",
        file_path=path,
        artifact_type=artifact_type,  # type: ignore[arg-type]
        size_bytes=1,
        sha256="abc",
        included=True,
        created_at=datetime.now(UTC),
    )
