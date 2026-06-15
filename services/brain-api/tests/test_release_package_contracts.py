"""Release package contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.release_package import (
    ReleasePackageFile,
    ReleasePackageRequest,
    SBOMPlaceholder,
)


def test_release_package_file_rejects_traversal() -> None:
    with pytest.raises(ValidationError):
        ReleasePackageFile(
            release_package_file_id="file-1",
            release_package_id="package-1",
            file_path="../secret.txt",
            artifact_type="source",
            size_bytes=1,
            sha256="abc",
            included=True,
        )


def test_release_package_file_requires_checksum_when_included() -> None:
    with pytest.raises(ValidationError):
        ReleasePackageFile(
            release_package_file_id="file-1",
            release_package_id="package-1",
            file_path="README.md",
            artifact_type="docs",
            size_bytes=1,
            sha256="",
            included=True,
        )


def test_release_package_request_rejects_unsafe_output_dir() -> None:
    with pytest.raises(ValidationError):
        ReleasePackageRequest(
            version="0.1.0",
            owner_scope=["workspace:main"],
            output_dir="/tmp/aion",
        )


def test_release_package_request_rejects_secret_metadata() -> None:
    with pytest.raises(ValueError, match="secret"):
        ReleasePackageRequest(
            version="0.1.0",
            owner_scope=["workspace:main"],
            metadata={"api_key": "nope"},
        )


def test_sbom_placeholder_rejects_secret_like_package_metadata() -> None:
    with pytest.raises(ValueError, match="secret"):
        SBOMPlaceholder(
            sbom_id="sbom-1",
            version="0.1.0",
            format="aion-local-json-placeholder",
            packages=[{"name": "pkg", "token": "hidden"}],
            generated_by="test",
            generated_at=datetime.now(UTC),
        )
