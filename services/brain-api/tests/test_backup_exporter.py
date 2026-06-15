"""Backup exporter tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.backups import BackupRequest
from tests.backup_fakes import SCOPE, DenyPolicy, FakeTelemetry, exporter


def test_backup_exporter_dry_run_persists_without_writing_files(tmp_path: Path) -> None:
    service = exporter(tmp_path)

    job = service.export(
        BackupRequest(
            owner_scope=SCOPE,
            resource_types=["events", "memory"],
            dry_run=True,
        )
    )

    assert job.status == "dry_run"
    assert job.manifest is not None
    assert job.manifest.total_record_count == 2
    assert not (tmp_path / job.output_dir).exists()
    assert service.get_job(job.backup_job_id, SCOPE) is not None


def test_backup_exporter_write_mode_writes_jsonl_and_manifest(tmp_path: Path) -> None:
    service = exporter(tmp_path)

    job = service.export(
        BackupRequest(
            owner_scope=SCOPE,
            resource_types=["memory"],
            dry_run=False,
        )
    )
    backup_dir = tmp_path / job.output_dir

    assert job.status == "completed"
    assert (backup_dir / "manifest.json").exists()
    assert (backup_dir / "checksums.json").exists()
    assert (backup_dir / "validation.json").exists()
    resource_text = (backup_dir / "resources/memory.jsonl").read_text(encoding="utf-8")
    assert "[REDACTED]" in resource_text
    assert "secret-value" not in resource_text


def test_backup_exporter_policy_deny_blocks_export(tmp_path: Path) -> None:
    service = exporter(tmp_path, policy=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        service.export(BackupRequest(owner_scope=SCOPE, resource_types=["events"]))


def test_backup_exporter_emits_visual_telemetry(tmp_path: Path) -> None:
    telemetry = FakeTelemetry()
    service = exporter(tmp_path, telemetry=telemetry)

    service.export(BackupRequest(owner_scope=SCOPE, resource_types=["events"]))

    event_types = {getattr(event, "event_type", "") for event in telemetry.events}
    assert {"backup_started", "backup_file_written", "backup_completed"} <= event_types
