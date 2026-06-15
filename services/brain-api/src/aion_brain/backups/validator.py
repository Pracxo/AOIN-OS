"""Validation service for local backups."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.backups.checksums import root_checksum, sha256_file
from aion_brain.backups.exporter import _is_relative_to
from aion_brain.backups.redaction import REDACTED, SENSITIVE_KEY_FRAGMENTS, strip_sensitive_metadata
from aion_brain.backups.repository import BackupRepository
from aion_brain.backups.resource_readers import RESOURCE_TYPES
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.backups import (
    BackupManifest,
    BackupValidationReport,
    BackupValidationStatus,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class BackupValidator:
    """Validate local backup manifests and resource files."""

    def __init__(
        self,
        backup_repository: BackupRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
        root_dir: Path | None = None,
    ) -> None:
        self._repository = backup_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._root_dir = root_dir or Path(__file__).parents[5]

    def validate_backup_job(self, backup_job_id: str, scope: list[str]) -> BackupValidationReport:
        """Validate a persisted backup job."""
        self._authorize("backup.validate", scope, resource_id=backup_job_id)
        job = self._repository.get_backup_job(backup_job_id)
        if job is None:
            raise AIONNotFoundException("backup_job_not_found")
        checks: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        if job.manifest is None:
            failures.append({"name": "manifest_present", "status": "failed"})
        else:
            _validate_manifest(job.manifest, checks, failures, warnings, self._settings.version)
            expected_root = root_checksum(job.checksums)
            if expected_root != job.manifest.root_checksum:
                failures.append({"name": "root_checksum", "status": "failed"})
            else:
                checks.append({"name": "root_checksum", "status": "passed"})
        if job.status != "dry_run":
            path = self._resolve_path(job.output_dir)
            _validate_backup_path(
                path,
                checks,
                failures,
                warnings,
                expected_job_id=job.backup_job_id,
                running_version=self._settings.version,
            )
        status = _status(failures, warnings)
        report = BackupValidationReport(
            report_id=f"backup-validation-{uuid4().hex}",
            backup_job_id=backup_job_id,
            backup_path=job.output_dir,
            status=status,
            checks=strip_sensitive_metadata_list(checks),
            failures=strip_sensitive_metadata_list(failures),
            warnings=strip_sensitive_metadata_list(warnings),
            generated_at=datetime.now(UTC),
        )
        self._emit("backup_validated", backup_job_id, scope, {"status": status})
        return report

    def validate_backup_path(self, backup_path: str, scope: list[str]) -> BackupValidationReport:
        """Validate a local backup path."""
        self._authorize("backup.validate", scope, resource_id=backup_path)
        path = self._resolve_path(backup_path)
        checks: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        _validate_backup_path(
            path,
            checks,
            failures,
            warnings,
            expected_job_id=None,
            running_version=self._settings.version,
        )
        status = _status(failures, warnings)
        report = BackupValidationReport(
            report_id=f"backup-validation-{uuid4().hex}",
            backup_job_id=None,
            backup_path=backup_path,
            status=status,
            checks=strip_sensitive_metadata_list(checks),
            failures=strip_sensitive_metadata_list(failures),
            warnings=strip_sensitive_metadata_list(warnings),
            generated_at=datetime.now(UTC),
        )
        self._emit("backup_validated", backup_path, scope, {"status": status})
        return report

    def _resolve_path(self, value: str) -> Path:
        path = (self._root_dir / value).resolve()
        if not _is_relative_to(path, self._root_dir.resolve()):
            raise AIONNotFoundException("backup_path_not_found")
        return path

    def _authorize(self, action_type: str, scope: list[str], *, resource_id: str | None) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type="backup",
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context={},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
        payload: dict[str, Any],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="backup",
            node_id=node_id,
            intensity=0.7,
            scope=scope,
            payload=strip_sensitive_metadata(payload),
        )


def _validate_backup_path(
    path: Path,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    *,
    expected_job_id: str | None,
    running_version: str,
) -> None:
    if not path.exists() or not path.is_dir():
        failures.append({"name": "backup_path_exists", "status": "failed"})
        return
    unsafe = [child for child in path.rglob("*") if child.name == ".env"]
    if unsafe:
        failures.append({"name": "unsafe_files_absent", "status": "failed"})
    else:
        checks.append({"name": "unsafe_files_absent", "status": "passed"})
    manifest_path = path / "manifest.json"
    checksums_path = path / "checksums.json"
    if not manifest_path.exists():
        failures.append({"name": "manifest_present", "status": "failed"})
        return
    manifest = BackupManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    if expected_job_id is not None and manifest.backup_id != expected_job_id:
        failures.append({"name": "manifest_backup_id", "status": "failed"})
    _validate_manifest(manifest, checks, failures, warnings, running_version)
    checksums = _load_checksums(checksums_path)
    for relative_path, expected in checksums.items():
        if not relative_path.startswith("resources/"):
            failures.append({"name": "resource_path", "status": "failed", "path": relative_path})
            continue
        file_path = path / relative_path
        if not file_path.exists():
            failures.append(
                {"name": "resource_file_present", "status": "failed", "path": relative_path}
            )
            continue
        if sha256_file(file_path) != expected:
            failures.append(
                {"name": "resource_checksum", "status": "failed", "path": relative_path}
            )
        else:
            checks.append({"name": "resource_checksum", "status": "passed", "path": relative_path})
        _validate_jsonl(file_path, manifest, failures, checks)
    if root_checksum(checksums) != manifest.root_checksum:
        failures.append({"name": "root_checksum", "status": "failed"})
    else:
        checks.append({"name": "root_checksum", "status": "passed"})


def _validate_manifest(
    manifest: BackupManifest,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    running_version: str,
) -> None:
    if not manifest.owner_scope:
        failures.append({"name": "owner_scope", "status": "failed"})
    else:
        checks.append({"name": "owner_scope", "status": "passed"})
    unsupported = [item for item in manifest.resource_types if item not in RESOURCE_TYPES]
    if unsupported:
        failures.append({"name": "resource_types_supported", "status": "failed"})
    else:
        checks.append({"name": "resource_types_supported", "status": "passed"})
    if manifest.version != running_version:
        warnings.append({"name": "version_match", "status": "warning"})
    else:
        checks.append({"name": "version_match", "status": "passed"})


def _validate_jsonl(
    path: Path,
    manifest: BackupManifest,
    failures: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> None:
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            failures.append({"name": "jsonl_parse", "status": "failed", "line": line_number})
            continue
        if isinstance(payload, dict) and manifest.redaction_mode != "none":
            if _contains_raw_secret_value(payload):
                failures.append(
                    {"name": "secret_material_absent", "status": "failed", "line": line_number}
                )
    checks.append({"name": "jsonl_parse", "status": "passed", "path": path.name})


def _contains_raw_secret_value(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS):
                if item != REDACTED:
                    return True
            if _contains_raw_secret_value(item):
                return True
    if isinstance(value, list):
        return any(_contains_raw_secret_value(item) for item in value)
    return False


def _load_checksums(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def _status(
    failures: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> BackupValidationStatus:
    if failures:
        return "failed"
    if warnings:
        return "warning"
    return "passed"


def strip_sensitive_metadata_list(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip secret-like keys from validation payload lists."""
    return [strip_sensitive_metadata(value) for value in values]
