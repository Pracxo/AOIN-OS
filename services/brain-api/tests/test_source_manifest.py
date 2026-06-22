"""Source manifest tests."""

from __future__ import annotations

from aion_brain.release_package.source_manifest import SourceManifestService
from tests.release_package_fakes import write_release_tree


def test_source_manifest_excludes_forbidden_and_oversized_files(tmp_path) -> None:
    write_release_tree(tmp_path)
    (tmp_path / "services/brain-api/src/.env").write_text("SECRET=1\n", encoding="utf-8")
    (tmp_path / "services/brain-api/src/token_helper.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "services/brain-api/src/.pytest_cache").mkdir(parents=True, exist_ok=True)
    (tmp_path / "services/brain-api/src/.pytest_cache/cache.py").write_text(
        "x = 1\n",
        encoding="utf-8",
    )
    (tmp_path / "services/brain-api/src/large.py").write_bytes(b"x" * 12)

    manifest = SourceManifestService(max_file_size_mb=0).build(tmp_path)

    paths = {file["file_path"] for file in manifest["files"]}
    excluded = {item["file_path"]: item["reason"] for item in manifest["excluded_artifacts"]}
    assert "README.md" not in paths
    assert excluded["services/brain-api/src/.env"] == "env_file"
    assert excluded["services/brain-api/src/token_helper.py"] == "secret_name"
    assert excluded["services/brain-api/src/.pytest_cache/cache.py"] == "cache_dir"
    assert excluded["services/brain-api/src/large.py"] == "oversized"
    assert manifest["root_checksum"]
