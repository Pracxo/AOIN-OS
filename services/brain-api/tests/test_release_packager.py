"""Release packager service tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.release_package import ReleasePackageRequest
from tests.release_package_fakes import SCOPE, FakeApp, packager, write_release_tree
from tests.versioning_fakes import DenyPolicy


def test_release_packager_dry_run_persists_record(tmp_path: Path) -> None:
    write_release_tree(tmp_path)
    service = packager(tmp_path)

    package = service.package(
        ReleasePackageRequest(
            version="0.1.0",
            owner_scope=SCOPE,
            dry_run=True,
            output_dir="artifacts/releases",
        ),
        app=FakeApp(),
    )

    fetched = service.get(package.release_package_id, SCOPE)
    assert package.status == "dry_run"
    assert package.manifest.metadata["external_calls"] is False
    assert fetched is not None
    assert fetched.release_package_id == package.release_package_id


def test_release_packager_writes_local_artifacts(tmp_path: Path) -> None:
    write_release_tree(tmp_path)
    service = packager(tmp_path)

    package = service.package(
        ReleasePackageRequest(
            version="0.1.0",
            owner_scope=SCOPE,
            dry_run=False,
            output_dir="artifacts/releases",
        ),
        app=FakeApp(),
    )

    package_dir = tmp_path / package.package_path
    assert package.status == "created"
    assert (package_dir / "release-package-manifest.json").is_file()
    assert (package_dir / "checksums.json").is_file()
    assert package_dir.with_suffix(".tar.gz").is_file()


def test_release_packager_policy_deny_blocks_create(tmp_path: Path) -> None:
    write_release_tree(tmp_path)
    service = packager(tmp_path, policy=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        service.package(
            ReleasePackageRequest(version="0.1.0", owner_scope=SCOPE),
            app=FakeApp(),
        )
