"""Backup contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.backups import (
    BackupFile,
    BackupManifest,
    BackupRequest,
    RestoreRequest,
)


def test_backup_request_rejects_unsafe_output_dir() -> None:
    with pytest.raises(ValidationError):
        BackupRequest(
            owner_scope=["workspace:main"],
            resource_types=["events"],
            output_dir="../outside",
        )


def test_backup_request_rejects_secret_metadata() -> None:
    with pytest.raises(ValueError, match="secret"):
        BackupRequest(
            owner_scope=["workspace:main"],
            resource_types=["events"],
            metadata={"api_key": "nope"},
        )


def test_backup_file_requires_checksum_when_included() -> None:
    with pytest.raises(ValidationError):
        BackupFile(
            backup_file_id="file-1",
            backup_job_id="backup-1",
            file_path="resources/events.jsonl",
            resource_type="events",
            record_count=1,
            size_bytes=10,
            sha256="",
            included=True,
        )


def test_restore_apply_requires_approval() -> None:
    with pytest.raises(ValidationError):
        RestoreRequest(
            restore_preview_id="preview-1",
            mode="apply",
            owner_scope=["workspace:main"],
        )


def test_manifest_requires_owner_scope_and_resources() -> None:
    with pytest.raises(ValidationError):
        BackupManifest(
            backup_id="backup-1",
            version="0.1.0",
            created_at=datetime.now(UTC),
            owner_scope=[],
            backup_type="scoped_local",
            resource_types=[],
            redaction_mode="redact_sensitive",
            file_count=0,
            total_record_count=0,
            total_size_bytes=0,
            root_checksum="abc",
            compatibility={},
            metadata={},
        )
