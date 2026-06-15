"""Release package security hardening report tests."""

from __future__ import annotations

from aion_brain.contracts.release_package import ReleasePackageFile, ReleasePackageRequest
from aion_brain.release_package.validator import ReleasePackageValidator


def test_release_package_validator_includes_hardening_report_when_available() -> None:
    validation = ReleasePackageValidator().validate(
        ReleasePackageRequest(version="0.1.0", owner_scope=["workspace:main"]),
        files=[
            ReleasePackageFile(
                release_package_file_id="file-1",
                release_package_id="package-1",
                file_path="README.md",
                artifact_type="docs",
                size_bytes=10,
                sha256="abc",
                included=True,
            ),
            ReleasePackageFile(
                release_package_file_id="file-2",
                release_package_id="package-1",
                file_path="AGENTS.md",
                artifact_type="docs",
                size_bytes=10,
                sha256="abc",
                included=True,
            ),
            ReleasePackageFile(
                release_package_file_id="file-3",
                release_package_id="package-1",
                file_path="CHANGELOG.md",
                artifact_type="changelog",
                size_bytes=10,
                sha256="abc",
                included=True,
            ),
        ],
        reports={"hardening_gate": {"status": "passed", "checks": []}},
    )

    assert any(check["name"] == "hardening_gate_report_included" for check in validation.checks)
