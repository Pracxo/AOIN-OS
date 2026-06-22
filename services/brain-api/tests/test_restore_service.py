"""Restore service tests."""

from __future__ import annotations

from pathlib import Path

from aion_brain.contracts.backups import BackupRequest, RestorePreviewRequest, RestoreRequest
from tests.backup_fakes import SCOPE, services


def test_restore_service_dry_run_records_no_writes(tmp_path: Path) -> None:
    _, exporter, preview_service, restore_service, _ = services(tmp_path)
    job = exporter.export(
        BackupRequest(owner_scope=SCOPE, resource_types=["events"], dry_run=False)
    )
    preview = preview_service.preview(
        RestorePreviewRequest(backup_path=job.output_dir, owner_scope=SCOPE)
    )

    restore_job = restore_service.restore(
        RestoreRequest(restore_preview_id=preview.restore_preview_id, owner_scope=SCOPE)
    )

    assert restore_job.status == "dry_run"
    assert restore_job.result["writes_performed"] == 0


def test_restore_service_apply_disabled_by_default(tmp_path: Path) -> None:
    _, exporter, preview_service, restore_service, _ = services(tmp_path)
    job = exporter.export(
        BackupRequest(owner_scope=SCOPE, resource_types=["events"], dry_run=False)
    )
    preview = preview_service.preview(
        RestorePreviewRequest(backup_path=job.output_dir, owner_scope=SCOPE)
    )

    restore_job = restore_service.restore(
        RestoreRequest(
            restore_preview_id=preview.restore_preview_id,
            mode="apply",
            approval_present=True,
            owner_scope=SCOPE,
        )
    )

    assert restore_job.status == "unsupported"
    assert restore_job.result["reason"] == "restore_apply_disabled_by_default"
