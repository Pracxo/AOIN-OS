"""Kernel wiring tests for versioning and freeze gate services."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_container_exposes_versioning_services() -> None:
    container = kernel_container()

    assert container.versioning_repository is not None
    assert container.version_manifest_service is not None
    assert container.feature_registry_service is not None
    assert container.compatibility_matrix_service is not None
    assert container.migration_baseline_service is not None
    assert container.release_artifact_service is not None
    assert container.sdk_compatibility_service is not None
    assert container.freeze_gate_service is not None


def test_kernel_diagnostics_include_versioning_flags() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "versioning_enabled" in names
    assert "freeze_gate_enabled" in names
