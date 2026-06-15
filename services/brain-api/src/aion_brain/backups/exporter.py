"""Application-level local backup exporter."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import (
    AIONPolicyDeniedException,
    AIONUnsupportedOperationException,
)
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.backups.checksums import root_checksum, sha256_jsonl_records
from aion_brain.backups.redaction import redact_record, strip_sensitive_metadata
from aion_brain.backups.repository import BackupRepository
from aion_brain.backups.resource_readers import (
    RESOURCE_TYPES,
    ResourceReaderRegistry,
    record_in_scope,
    record_is_deleted,
)
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.backups import (
    BackupFile,
    BackupJob,
    BackupManifest,
    BackupRequest,
    BackupResourceType,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class BackupExporter:
    """Export local AION state using public application boundaries."""

    def __init__(
        self,
        backup_repository: BackupRepository,
        resource_readers: ResourceReaderRegistry,
        policy_adapter: PolicyAdapter,
        *,
        autonomy_governor: object | None = None,
        risk_engine: object | None = None,
        approval_service: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
        root_dir: Path | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = backup_repository
        self._readers = resource_readers
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._root_dir = root_dir or Path(__file__).parents[5]
        self._audit_sink = audit_sink

    def export(self, request: BackupRequest) -> BackupJob:
        """Create a dry-run or write-mode local backup job."""
        if not self._settings.backups_enabled:
            raise AIONUnsupportedOperationException("backups_disabled")
        self._authorize(
            "backup.create",
            request.owner_scope,
            actor_id=request.actor_id or request.created_by,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            risk_level="medium",
            approval_present=True,
            context={
                "dry_run": request.dry_run,
                "backup_type": request.backup_type,
                "redaction_mode": request.redaction_mode,
            },
        )
        backup_job_id = request.backup_job_id or f"backup-{uuid4().hex}"
        created_at = datetime.now(UTC)
        self._emit(
            "backup_started",
            "backup",
            backup_job_id,
            request.owner_scope,
            0.5,
            {"dry_run": request.dry_run, "backup_type": request.backup_type},
        )
        autonomy = _optional_decision(
            self._autonomy_governor,
            "decide",
            action_type="backup.create",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
        )
        if _decision_denied(autonomy):
            job = self._blocked_job(
                request,
                backup_job_id,
                "blocked_by_autonomy",
                created_at,
                {"reason": _decision_reason(autonomy, "autonomy_denied")},
            )
            return self._repository.save_backup_job(job)
        risk = _optional_decision(
            self._risk_engine,
            "assess",
            action_type="backup.create",
            risk_level="medium",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
        )
        approval = _optional_decision(
            self._approval_service,
            "prepare",
            action_type="backup.create",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
        )
        output_path = self._backup_path(request.output_dir, backup_job_id)
        resources = self._selected_resources(request)
        files: list[BackupFile] = []
        warnings: list[dict[str, Any]] = []
        resource_payloads: dict[BackupResourceType, list[dict[str, Any]]] = {}
        checksums: dict[str, str] = {}
        total_size = 0
        total_records = 0
        for resource_type in resources:
            records, resource_warnings = self._prepare_resource(resource_type, request)
            warnings.extend(resource_warnings)
            if resource_type == "visual_telemetry" and not request.include_visual_telemetry:
                files.append(
                    _backup_file(
                        backup_job_id,
                        resource_type,
                        f"resources/{resource_type}.jsonl",
                        [],
                        included=False,
                        reason="visual_telemetry_excluded_by_request",
                    )
                )
                continue
            resource_payloads[resource_type] = records
            file_path = f"resources/{resource_type}.jsonl"
            checksum = sha256_jsonl_records(records)
            encoded = _jsonl_bytes(records)
            checksums[file_path] = checksum
            total_size += len(encoded)
            total_records += len(records)
            files.append(
                BackupFile(
                    backup_file_id=f"backup-file-{uuid4().hex}",
                    backup_job_id=backup_job_id,
                    file_path=file_path,
                    resource_type=resource_type,
                    record_count=len(records),
                    size_bytes=len(encoded),
                    sha256=checksum,
                    included=True,
                    reason=None,
                    created_at=created_at,
                )
            )
            self._emit(
                "backup_file_written",
                "backup_file",
                f"{backup_job_id}:{resource_type}",
                request.owner_scope,
                0.65,
                {
                    "dry_run": request.dry_run,
                    "resource_type": resource_type,
                    "record_count": len(records),
                },
            )
        root = root_checksum(checksums)
        manifest = BackupManifest(
            backup_id=backup_job_id,
            version=self._settings.version,
            created_at=created_at,
            created_by=request.created_by,
            owner_scope=request.owner_scope,
            backup_type="dry_run" if request.dry_run else request.backup_type,
            resource_types=resources,
            redaction_mode=request.redaction_mode,
            file_count=len([file for file in files if file.included]),
            total_record_count=total_records,
            total_size_bytes=total_size,
            root_checksum=root,
            compatibility={
                "api_version": self._settings.api_version,
                "application_level": True,
                "direct_database_restore": False,
            },
            metadata=strip_sensitive_metadata(
                {
                    "local_only": True,
                    "dry_run": request.dry_run,
                    "include_deleted": request.include_deleted,
                    "warnings": warnings,
                    **request.metadata,
                }
            ),
        )
        result = {
            "dry_run": request.dry_run,
            "backup_path": output_path.as_posix(),
            "resource_count": len(resources),
            "record_count": total_records,
            "warnings": warnings,
            "risk": _jsonable(risk),
            "approval": _jsonable(approval),
        }
        job = BackupJob(
            backup_job_id=backup_job_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="dry_run" if request.dry_run else "completed",
            backup_type=request.backup_type,
            owner_scope=request.owner_scope,
            resource_types=resources,
            redaction_mode=request.redaction_mode,
            output_dir=output_path.relative_to(self._root_dir.resolve()).as_posix(),
            manifest=manifest,
            files=sorted(files, key=lambda item: item.file_path),
            checksums=checksums,
            result=strip_sensitive_metadata(result),
            created_by=request.created_by,
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )
        if not request.dry_run:
            self._write_backup(job, output_path, resource_payloads)
        saved = self._repository.save_backup_job(job)
        record_audit_event(
            self._audit_sink,
            action_type="backup.create",
            resource_type="backup",
            resource_id=saved.backup_job_id,
            event_type="backup_completed",
            outcome="dry_run" if saved.status == "dry_run" else "completed",
            source_component="backup_exporter",
            trace_id=saved.trace_id,
            actor_id=saved.actor_id,
            workspace_id=saved.workspace_id,
            payload={
                "status": saved.status,
                "resource_count": len(saved.resource_types),
                "file_count": len(saved.files),
                "redaction_mode": saved.redaction_mode,
            },
        )
        self._emit(
            "backup_completed",
            "backup",
            backup_job_id,
            request.owner_scope,
            0.9,
            {"status": saved.status, "record_count": total_records},
        )
        return saved

    def get_job(self, backup_job_id: str, scope: list[str]) -> BackupJob | None:
        """Return one policy-authorized backup job."""
        self._authorize(
            "backup.read",
            scope,
            resource_id=backup_job_id,
            risk_level="low",
        )
        job = self._repository.get_backup_job(backup_job_id)
        if job is None or not set(job.owner_scope) & set(scope):
            return None
        return job

    def list_jobs(
        self,
        scope: list[str],
        *,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[BackupJob]:
        """List policy-authorized backup jobs."""
        self._authorize("backup.read", scope, risk_level="low")
        return [
            job
            for job in self._repository.list_backup_jobs(
                workspace_id=workspace_id,
                status=status,
            )
            if set(job.owner_scope) & set(scope)
        ]

    def _selected_resources(self, request: BackupRequest) -> list[BackupResourceType]:
        if request.backup_type == "full_local":
            return list(RESOURCE_TYPES)
        return list(request.resource_types)

    def _prepare_resource(
        self,
        resource_type: BackupResourceType,
        request: BackupRequest,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        result = self._readers.read(
            resource_type,
            request.owner_scope,
            explicit=request.backup_type == "resource_subset",
        )
        prepared: list[dict[str, Any]] = []
        for record in result.records:
            if not record_in_scope(record, request.owner_scope):
                continue
            if not request.include_deleted and record_is_deleted(record):
                continue
            redacted = redact_record(record, request.redaction_mode)
            if redacted is None:
                continue
            prepared.append(redacted)
            if len(prepared) >= request.max_records_per_resource:
                break
        return prepared, result.warnings

    def _write_backup(
        self,
        job: BackupJob,
        output_path: Path,
        resource_payloads: dict[BackupResourceType, list[dict[str, Any]]],
    ) -> None:
        output_path.mkdir(parents=True, exist_ok=True)
        resources_dir = output_path / "resources"
        resources_dir.mkdir(exist_ok=True)
        for resource_type, records in sorted(resource_payloads.items()):
            (resources_dir / f"{resource_type}.jsonl").write_bytes(_jsonl_bytes(records))
        manifest_payload = job.manifest.model_dump(mode="json") if job.manifest else {}
        (output_path / "manifest.json").write_text(
            json.dumps(manifest_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        (output_path / "checksums.json").write_text(
            json.dumps(job.checksums, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validation = {
            "status": "passed",
            "backup_job_id": job.backup_job_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "checks": [{"name": "export_completed", "status": "passed"}],
            "warnings": job.result.get("warnings", []),
        }
        (output_path / "validation.json").write_text(
            json.dumps(validation, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _backup_path(self, output_dir: str, backup_job_id: str) -> Path:
        output_root = (self._root_dir / output_dir).resolve()
        root = self._root_dir.resolve()
        if not _is_relative_to(output_root, root):
            raise AIONUnsupportedOperationException("backup_output_outside_repo")
        return output_root / backup_job_id

    def _blocked_job(
        self,
        request: BackupRequest,
        backup_job_id: str,
        status: str,
        created_at: datetime,
        result: dict[str, Any],
    ) -> BackupJob:
        return BackupJob(
            backup_job_id=backup_job_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            backup_type=request.backup_type,
            owner_scope=request.owner_scope,
            resource_types=list(request.resource_types),
            redaction_mode=request.redaction_mode,
            output_dir=request.output_dir,
            manifest=None,
            files=[],
            checksums={},
            result=strip_sensitive_metadata(result),
            created_by=request.created_by,
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        trace_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        approval_present: bool = False,
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="backup",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
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


def _backup_file(
    backup_job_id: str,
    resource_type: BackupResourceType,
    file_path: str,
    records: list[dict[str, Any]],
    *,
    included: bool,
    reason: str | None,
) -> BackupFile:
    encoded = _jsonl_bytes(records)
    return BackupFile(
        backup_file_id=f"backup-file-{uuid4().hex}",
        backup_job_id=backup_job_id,
        file_path=file_path,
        resource_type=resource_type,
        record_count=len(records),
        size_bytes=len(encoded),
        sha256=sha256_jsonl_records(records) if included else "",
        included=included,
        reason=reason,
        created_at=datetime.now(UTC),
    )


def _jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    sorted_records = sorted(
        records,
        key=lambda item: json.dumps(item, sort_keys=True, default=str),
    )
    lines = [
        json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
        for record in sorted_records
    ]
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")


def _optional_decision(service: object | None, method_name: str, **payload: Any) -> object | None:
    method = getattr(service, method_name, None)
    if not callable(method):
        return None
    try:
        return cast(object, method(payload))
    except TypeError:
        try:
            return cast(object, method(**payload))
        except Exception:
            return None
    except Exception:
        return None


def _decision_denied(value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, dict):
        if value.get("allow") is False:
            return True
        if value.get("decision") in {"deny", "blocked"}:
            return True
    allow = getattr(value, "allow", None)
    if allow is False:
        return True
    decision = getattr(value, "decision", None)
    return decision in {"deny", "blocked"}


def _decision_reason(value: object | None, default: str) -> str:
    if isinstance(value, dict) and value.get("reason") is not None:
        return str(value["reason"])
    reason = getattr(value, "reason", None)
    return str(reason) if reason is not None else default


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
