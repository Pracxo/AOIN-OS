"""Repository-level architecture boundary guard."""

from pathlib import Path

from aion_brain.kernel.boundary_check import ArchitectureBoundaryChecker


def test_brain_source_has_no_direct_vendor_leakage() -> None:
    source_root = Path(__file__).parents[1] / "src" / "aion_brain"
    report = ArchitectureBoundaryChecker(source_root).check()
    assert report.status == "passed", report.violations
