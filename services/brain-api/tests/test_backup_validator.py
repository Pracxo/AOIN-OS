"""Backup validator tests."""

from __future__ import annotations

from pathlib import Path

from aion_brain.contracts.backups import BackupRequest
from tests.backup_fakes import SCOPE, services


def test_backup_validator_passes_written_backup(tmp_path: Path) -> None:
    _, exporter, _, _, validator = services(tmp_path)
    job = exporter.export(
        BackupRequest(owner_scope=SCOPE, resource_types=["events"], dry_run=False)
    )

    report = validator.validate_backup_path(job.output_dir, SCOPE)

    assert report.status == "passed"
    assert not report.failures


def test_backup_validator_detects_checksum_mismatch(tmp_path: Path) -> None:
    _, exporter, _, _, validator = services(tmp_path)
    job = exporter.export(
        BackupRequest(owner_scope=SCOPE, resource_types=["events"], dry_run=False)
    )
    (tmp_path / job.output_dir / "resources/events.jsonl").write_text(
        '{"event_id":"changed"}\n',
        encoding="utf-8",
    )

    report = validator.validate_backup_path(job.output_dir, SCOPE)

    assert report.status == "failed"
    assert any(failure["name"] == "resource_checksum" for failure in report.failures)
