"""Restore preview planner for local backups."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.backups.checksums import sha256_file
from aion_brain.backups.exporter import (
    _decision_denied,
    _decision_reason,
    _is_relative_to,
    _optional_decision,
)
from aion_brain.backups.redaction import contains_sensitive_key, strip_sensitive_metadata
from aion_brain.backups.repository import BackupRepository
from aion_brain.backups.resource_readers import (
    RESOURCE_TYPES,
    ResourceReaderRegistry,
    record_identifier,
    record_scope_values,
)
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.backups import (
    BackupManifest,
    BackupResourceType,
    RestoreConflict,
    RestorePreview,
    RestorePreviewRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class RestorePreviewService:
    """Build conflict-aware restore previews without applying data."""

    def __init__(
        self,
        backup_repository: BackupRepository,
        policy_adapter: PolicyAdapter,
        resource_readers: ResourceReaderRegistry,
        *,
        autonomy_governor: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
        root_dir: Path | None = None,
    ) -> None:
        self._repository = backup_repository
        self._policy_adapter = policy_adapter
        self._readers = resource_readers
        self._autonomy_governor = autonomy_governor
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._root_dir = root_dir or Path(__file__).parents[5]

    def preview(self, request: RestorePreviewRequest) -> RestorePreview:
        """Create and persist a restore preview."""
        self._authorize(
            "backup.restore.preview",
            request.owner_scope,
            actor_id=request.actor_id or request.created_by,
            workspace_id=request.workspace_id,
            risk_level="low",
            context={"conflict_strategy": request.conflict_strategy},
        )
        preview_id = request.restore_preview_id or f"restore-preview-{uuid4().hex}"
        created_at = datetime.now(UTC)
        self._emit(
            "restore_preview_started",
            "restore_preview",
            preview_id,
            request.owner_scope,
            0.5,
            {"backup_job_id": request.backup_job_id},
        )
        autonomy = _optional_decision(
            self._autonomy_governor,
            "decide",
            action_type="backup.restore.preview",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
        )
        if _decision_denied(autonomy):
            preview = RestorePreview(
                restore_preview_id=preview_id,
                backup_job_id=request.backup_job_id,
                trace_id=None,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                status="blocked_by_autonomy",
                input_manifest=None,
                conflict_count=0,
                missing_dependency_count=0,
                records_seen=0,
                records_restorable=0,
                records_blocked=0,
                conflicts=[],
                plan={"reason": _decision_reason(autonomy, "autonomy_denied")},
                created_by=request.created_by,
                created_at=created_at,
                completed_at=datetime.now(UTC),
            )
            return self._repository.save_restore_preview(preview)
        manifest, records, load_warnings, backup_path = self._load_backup(request)
        resource_types = request.resource_types or manifest.resource_types
        conflicts = self._conflicts(manifest, records, resource_types, request, backup_path)
        conflicts.extend(load_warnings)
        missing_dependencies = [
            conflict for conflict in conflicts if conflict.conflict_type == "dependency_missing"
        ]
        blocked_ids = {conflict.record_id for conflict in conflicts}
        records_seen = sum(len(values) for values in records.values())
        status = "warning" if conflicts else "passed"
        if any(conflict.severity == "critical" for conflict in conflicts):
            status = "failed"
        preview = RestorePreview(
            restore_preview_id=preview_id,
            backup_job_id=request.backup_job_id or manifest.backup_id,
            trace_id=None,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            input_manifest=manifest,
            conflict_count=len(conflicts),
            missing_dependency_count=len(missing_dependencies),
            records_seen=records_seen,
            records_restorable=max(records_seen - len(blocked_ids), 0),
            records_blocked=len(blocked_ids),
            conflicts=conflicts,
            plan=strip_sensitive_metadata(
                {
                    "mode": "preview_only",
                    "conflict_strategy": request.conflict_strategy,
                    "resource_types": list(resource_types),
                    "backup_path": backup_path.as_posix() if backup_path else None,
                    "restore_apply_enabled": self._settings.backup_restore_apply_enabled,
                }
            ),
            created_by=request.created_by,
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_restore_preview(preview)
        self._emit(
            "restore_preview_completed",
            "restore_preview",
            saved.restore_preview_id,
            request.owner_scope,
            0.8 if saved.status != "failed" else 1.0,
            {"status": saved.status, "conflict_count": saved.conflict_count},
        )
        return saved

    def get_preview(self, restore_preview_id: str, scope: list[str]) -> RestorePreview | None:
        """Return one preview after policy authorization."""
        self._authorize(
            "backup.restore.preview",
            scope,
            resource_id=restore_preview_id,
            risk_level="low",
        )
        preview = self._repository.get_restore_preview(restore_preview_id)
        if preview is None:
            return None
        manifest_scope = preview.input_manifest.owner_scope if preview.input_manifest else scope
        if not set(manifest_scope) & set(scope):
            return None
        return preview

    def _load_backup(
        self,
        request: RestorePreviewRequest,
    ) -> tuple[
        BackupManifest,
        dict[BackupResourceType, list[dict[str, Any]]],
        list[RestoreConflict],
        Path | None,
    ]:
        backup_path: Path | None = None
        if request.backup_job_id:
            job = self._repository.get_backup_job(request.backup_job_id)
            if job is None or job.manifest is None:
                raise AIONNotFoundException("backup_job_not_found")
            manifest = job.manifest
            backup_path = self._resolve_path(job.output_dir) if job.status != "dry_run" else None
        elif request.backup_path:
            backup_path = self._resolve_path(request.backup_path)
            manifest = _load_manifest(backup_path / "manifest.json")
        else:
            raise AIONNotFoundException("backup_source_not_found")
        records: dict[BackupResourceType, list[dict[str, Any]]] = {}
        warnings: list[RestoreConflict] = []
        if backup_path is not None:
            checksums = _load_checksums(backup_path / "checksums.json")
            for resource_type in request.resource_types or manifest.resource_types:
                path = backup_path / "resources" / f"{resource_type}.jsonl"
                expected = checksums.get(f"resources/{resource_type}.jsonl")
                if not path.exists():
                    records[resource_type] = []
                    continue
                if expected is not None and sha256_file(path) != expected:
                    warnings.append(
                        _conflict(
                            resource_type,
                            record_id=f"{resource_type}:checksum",
                            conflict_type="checksum_mismatch",
                            severity="critical",
                            reason="resource checksum does not match manifest",
                        )
                    )
                records[resource_type] = _load_jsonl(path)
        else:
            for resource_type in request.resource_types or manifest.resource_types:
                records[resource_type] = []
        return manifest, records, warnings, backup_path

    def _conflicts(
        self,
        manifest: BackupManifest,
        records: dict[BackupResourceType, list[dict[str, Any]]],
        resource_types: list[BackupResourceType],
        request: RestorePreviewRequest,
        backup_path: Path | None,
    ) -> list[RestoreConflict]:
        conflicts: list[RestoreConflict] = []
        if manifest.version != self._settings.version:
            conflicts.append(
                _conflict(
                    "kernel_records",
                    record_id=manifest.backup_id,
                    conflict_type="version_mismatch",
                    severity="medium",
                    reason="backup version differs from running AION version",
                )
            )
        if not set(manifest.owner_scope) & set(request.owner_scope):
            conflicts.append(
                _conflict(
                    "kernel_records",
                    record_id=manifest.backup_id,
                    conflict_type="scope_mismatch",
                    severity="high",
                    reason="backup owner_scope does not overlap request scope",
                )
            )
        for resource_type in resource_types:
            if resource_type not in RESOURCE_TYPES:
                conflicts.append(
                    _conflict(
                        resource_type,
                        record_id=str(resource_type),
                        conflict_type="unsupported_resource",
                        severity="critical",
                        reason="resource type is not supported by AION backup v0.1",
                    )
                )
        incoming_ids = {
            record_id
            for values in records.values()
            for record in values
            if (record_id := record_identifier(record)) is not None
        }
        existing_by_resource = {
            resource_type: self._readers.existing_ids(resource_type, request.owner_scope)
            for resource_type in resource_types
            if resource_type in RESOURCE_TYPES
        }
        all_existing = (
            set().union(*existing_by_resource.values()) if existing_by_resource else set()
        )
        for resource_type, values in records.items():
            existing_ids = existing_by_resource.get(resource_type, set())
            for record in values:
                record_id = record_identifier(record) or f"{resource_type}:{uuid4().hex}"
                if record_id in existing_ids:
                    conflicts.append(
                        _conflict(
                            resource_type,
                            record_id=record_id,
                            conflict_type="id_exists",
                            severity="medium",
                            existing_ref=record_id,
                            incoming_ref=record_id,
                            reason="incoming record id already exists",
                        )
                    )
                record_scope = record_scope_values(record)
                if record_scope and not set(record_scope) & set(request.owner_scope):
                    conflicts.append(
                        _conflict(
                            resource_type,
                            record_id=record_id,
                            conflict_type="scope_mismatch",
                            severity="high",
                            reason="incoming record scope does not overlap request scope",
                        )
                    )
                if manifest.redaction_mode == "none" and contains_sensitive_key(record):
                    conflicts.append(
                        _conflict(
                            resource_type,
                            record_id=record_id,
                            conflict_type="sensitive_data_blocked",
                            severity="critical",
                            reason=(
                                "unredacted sensitive-looking keys are not restorable by default"
                            ),
                        )
                    )
                for dependency_id in _dependency_ids(record):
                    if dependency_id not in incoming_ids and dependency_id not in all_existing:
                        conflicts.append(
                            _conflict(
                                resource_type,
                                record_id=record_id,
                                conflict_type="dependency_missing",
                                severity="high",
                                incoming_ref=dependency_id,
                                reason="record dependency is not present in backup or local state",
                            )
                        )
        if backup_path is not None and not (backup_path / "manifest.json").exists():
            conflicts.append(
                _conflict(
                    "kernel_records",
                    record_id=manifest.backup_id,
                    conflict_type="checksum_mismatch",
                    severity="critical",
                    reason="manifest file is missing",
                )
            )
        return conflicts

    def _resolve_path(self, value: str) -> Path:
        path = (self._root_dir / value).resolve()
        if not _is_relative_to(path, self._root_dir.resolve()):
            raise AIONNotFoundException("backup_path_not_found")
        return path

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="restore_preview",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        scope: list[str],
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=intensity,
            scope=scope,
            payload=strip_sensitive_metadata(payload),
        )


def _load_manifest(path: Path) -> BackupManifest:
    if not path.exists():
        raise AIONNotFoundException("backup_manifest_not_found")
    return BackupManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _load_checksums(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if isinstance(payload, dict):
                records.append(payload)
    return records


def _dependency_ids(record: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("depends_on", "refs"):
        item = record.get(key)
        if isinstance(item, list):
            values.extend(str(value) for value in item if str(value).strip())
    return values


def _conflict(
    resource_type: BackupResourceType,
    *,
    record_id: str,
    conflict_type: str,
    severity: str,
    reason: str,
    existing_ref: str | None = None,
    incoming_ref: str | None = None,
) -> RestoreConflict:
    return RestoreConflict(
        conflict_id=f"restore-conflict-{uuid4().hex}",
        resource_type=resource_type,
        record_id=record_id,
        conflict_type=cast(Any, conflict_type),
        severity=cast(Any, severity),
        existing_ref=existing_ref,
        incoming_ref=incoming_ref,
        reason=reason,
        resolution_options=["skip_conflicts", "require_manual"],
        metadata={},
    )
