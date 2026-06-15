"""MCP architecture boundary tests."""

from pathlib import Path

from aion_brain.kernel.boundary_check import ArchitectureBoundaryChecker


def test_boundary_checker_catches_direct_mcp_import_outside_compat(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("import mcp\n", encoding="utf-8")

    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "failed"
    assert any(item["type"] == "vendor_import_outside_adapter" for item in report.violations)


def test_boundary_checker_catches_subprocess_in_mcp_runtime_path(tmp_path: Path) -> None:
    module_dir = tmp_path / "modules"
    module_dir.mkdir()
    (module_dir / "mcp_runtime.py").write_text("import subprocess\n", encoding="utf-8")

    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "failed"
    assert any(item["type"] == "banned_import" for item in report.violations)
