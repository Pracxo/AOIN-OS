"""Dependency metadata scanner tests."""

from __future__ import annotations

from aion_brain.security_baseline.dependency_metadata import DependencyMetadataScanner


def test_dependency_metadata_scanner_reads_pyproject_without_network(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "x"\ndependencies = ["fastapi>=0"]\n',
        encoding="utf-8",
    )

    findings = DependencyMetadataScanner(root_dir=tmp_path).scan([pyproject])

    assert findings == []


def test_dependency_metadata_scanner_flags_provider_sdk_in_required_core_dependencies(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\ndependencies = ["openai>=1"]\n', encoding="utf-8")

    findings = DependencyMetadataScanner(root_dir=tmp_path).scan([pyproject])

    assert findings[0].category == "provider_sdk_required"
