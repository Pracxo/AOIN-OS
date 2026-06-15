"""SBOM placeholder tests."""

from __future__ import annotations

from aion_brain.release_package.sbom import SBOMPlaceholderService
from tests.release_package_fakes import write_release_tree


def test_sbom_placeholder_reads_local_project_metadata(tmp_path) -> None:
    write_release_tree(tmp_path)

    sbom = SBOMPlaceholderService(tmp_path).generate("0.1.0")

    assert sbom.format == "aion-local-json-placeholder"
    assert sbom.version == "0.1.0"
    assert {package["name"] for package in sbom.packages if package["present"]} == {
        "aion-brain-api",
        "aion-sdk-python",
    }
    assert sbom.limitations
