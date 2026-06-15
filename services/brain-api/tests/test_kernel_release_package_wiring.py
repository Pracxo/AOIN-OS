"""Kernel wiring tests for release package services."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_container_exposes_release_packager_services() -> None:
    container = kernel_container()

    assert container.release_package_repository is not None
    assert container.release_package_source_manifest_service is not None
    assert container.release_package_sbom_service is not None
    assert container.release_package_validator is not None
    assert container.release_handoff_service is not None
    assert container.release_packager is not None


def test_kernel_diagnostics_include_release_packaging_flags() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "release_packager_present" in names
    assert "release_package_validator_present" in names
    assert "release_packaging_enabled" in names
    assert "release_package_output_dir_configured" in names
    assert "release_package_sbom_placeholder_enabled" in names
