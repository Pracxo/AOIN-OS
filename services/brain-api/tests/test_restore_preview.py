"""Restore preview service tests."""

from __future__ import annotations

from pathlib import Path

from aion_brain.contracts.backups import BackupRequest, RestorePreviewRequest
from tests.backup_fakes import SCOPE, readers, services


def test_restore_preview_detects_id_conflict(tmp_path: Path) -> None:
    registry = readers(
        {
            "memory": [
                {
                    "memory_id": "memory-1",
                    "owner_scope": SCOPE,
                    "summary": "existing local memory",
                }
            ]
        }
    )
    _, exporter, preview_service, _, _ = services(tmp_path, registry=registry)
    job = exporter.export(
        BackupRequest(owner_scope=SCOPE, resource_types=["memory"], dry_run=False)
    )

    preview = preview_service.preview(
        RestorePreviewRequest(backup_path=job.output_dir, owner_scope=SCOPE)
    )

    assert preview.status == "warning"
    assert any(conflict.conflict_type == "id_exists" for conflict in preview.conflicts)


def test_restore_preview_detects_missing_dependency(tmp_path: Path) -> None:
    registry = readers(
        {
            "events": [
                {
                    "event_id": "event-1",
                    "owner_scope": SCOPE,
                    "depends_on": ["missing-record"],
                }
            ]
        }
    )
    _, exporter, preview_service, _, _ = services(tmp_path, registry=registry)
    job = exporter.export(
        BackupRequest(owner_scope=SCOPE, resource_types=["events"], dry_run=False)
    )

    preview = preview_service.preview(
        RestorePreviewRequest(backup_path=job.output_dir, owner_scope=SCOPE)
    )

    assert preview.missing_dependency_count == 1
    assert any(conflict.conflict_type == "dependency_missing" for conflict in preview.conflicts)
