"""Sandbox boundary checker tests."""

from aion_brain.kernel.boundary_check import ArchitectureBoundaryChecker


def test_boundary_checker_catches_forbidden_docker_import_outside_adapter(tmp_path) -> None:
    (tmp_path / "bad.py").write_text("import docker\n", encoding="utf-8")

    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "failed"
    assert report.violations[0]["type"] == "vendor_import_outside_adapter"


def test_boundary_checker_allows_docker_adapter_path(tmp_path) -> None:
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    (sandbox_dir / "docker_adapter.py").write_text("import docker\n", encoding="utf-8")

    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "passed"


def test_boundary_checker_catches_subprocess_in_sandbox_code(tmp_path) -> None:
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    (sandbox_dir / "bad.py").write_text("import subprocess\n", encoding="utf-8")

    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "failed"
    assert report.violations[0]["type"] == "banned_import"
