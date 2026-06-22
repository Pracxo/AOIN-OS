"""Release artifact manifest tests."""

from __future__ import annotations

from pathlib import Path

from aion_brain.versioning.artifacts import ReleaseArtifactService
from tests.versioning_fakes import SCOPE, AllowPolicy, repository, write_minimal_release_docs


def test_release_artifact_manifest_is_complete_when_required_files_exist(tmp_path: Path) -> None:
    write_minimal_release_docs(tmp_path)
    service = ReleaseArtifactService(repository(), AllowPolicy(), root_dir=tmp_path)

    manifest = service.generate("0.1.0", "tester", SCOPE)

    assert manifest.status == "complete"
    assert "README.md" in manifest.checksums
    assert manifest.report["packaged"] is False
    assert manifest.report["external_calls"] is False


def test_release_artifact_manifest_reports_missing_files(tmp_path: Path) -> None:
    service = ReleaseArtifactService(repository(), AllowPolicy(), root_dir=tmp_path)

    manifest = service.generate("0.1.0", "tester", SCOPE)

    assert manifest.status == "failed"
    assert "README.md" in manifest.report["missing_files"]
