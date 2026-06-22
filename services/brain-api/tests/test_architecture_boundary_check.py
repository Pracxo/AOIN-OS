"""Architecture boundary checker tests."""

from aion_brain.kernel.boundary_check import ArchitectureBoundaryChecker


def test_boundary_checker_catches_vendor_import_and_domain_directory(tmp_path) -> None:
    (tmp_path / "bad.py").write_text("import langgraph\n", encoding="utf-8")
    (tmp_path / "finance").mkdir()
    report = ArchitectureBoundaryChecker(tmp_path).check()
    assert report.status == "failed"
    assert {item["type"] for item in report.violations} == {
        "domain_directory",
        "vendor_import_outside_adapter",
    }


def test_boundary_checker_passes_clean_tree(tmp_path) -> None:
    (tmp_path / "clean.py").write_text("from pathlib import Path\n", encoding="utf-8")
    assert ArchitectureBoundaryChecker(tmp_path).check().status == "passed"


def test_boundary_checker_allows_turbovec_only_in_compat_boundary(tmp_path) -> None:
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "turbovec_compat.py").write_text(
        "import turbovec\n",
        encoding="utf-8",
    )
    assert ArchitectureBoundaryChecker(tmp_path).check().status == "passed"

    (memory_dir / "direct_turbovec.py").write_text(
        "import turbovec\n",
        encoding="utf-8",
    )
    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "failed"
    assert report.violations[0]["type"] == "vendor_import_outside_adapter"


def test_boundary_checker_flags_domain_policy_defaults(tmp_path) -> None:
    policy_dir = tmp_path / "policy_catalog"
    policy_dir.mkdir()
    (policy_dir / "defaults.py").write_text(
        'DEFAULT_ACTION_SPECS = (("finance.trade", "policy", "policy", "high"),)\n',
        encoding="utf-8",
    )

    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "failed"
    assert report.violations[0]["type"] == "domain_policy_default"


def test_boundary_checker_flags_raw_opa_http_usage(tmp_path) -> None:
    (tmp_path / "bad_opa.py").write_text(
        'import httpx\nOPA_URL = "http://opa:8181"\n',
        encoding="utf-8",
    )

    report = ArchitectureBoundaryChecker(tmp_path).check()

    assert report.status == "failed"
    assert report.violations[0]["type"] == "raw_opa_http_usage"
