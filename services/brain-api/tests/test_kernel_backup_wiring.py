"""Kernel wiring tests for local backup services."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_container_exposes_backup_services() -> None:
    container = kernel_container()

    assert container.backup_repository is not None
    assert container.backup_resource_readers is not None
    assert container.backup_exporter is not None
    assert container.restore_preview_service is not None
    assert container.restore_service is not None
    assert container.backup_validator is not None


def test_kernel_diagnostics_include_backup_flags() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "backup_exporter_present" in names
    assert "restore_preview_service_present" in names
    assert "backups_enabled" in names
    assert "backup_output_dir_configured" in names
    assert "backup_restore_apply_disabled_by_default" in names
