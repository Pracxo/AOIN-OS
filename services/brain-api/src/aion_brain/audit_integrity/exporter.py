"""Local audit export service."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from aion_brain.audit_integrity.canonical import canonical_json
from aion_brain.audit_integrity.hashing import sha256_text
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.audit_integrity.redaction import redact_audit_payload
from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.contracts.audit_integrity import AuditEntry, AuditExportRecord, AuditExportRequest
from aion_brain.contracts.policy import PolicyRequest


class AuditExporter:
    """Export audit entries to local files only."""

    def __init__(
        self,
        repository: AuditIntegrityRepository,
        policy_adapter: object | None,
        *,
        autonomy_governor: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def export(self, request: AuditExportRequest) -> AuditExportRecord:
        """Export audit entries or return a dry-run plan."""
        export_id = request.audit_export_id or f"audit-export-{uuid4().hex}"
        if not self._allowed(request):
            return self._persist_record(
                request,
                export_id,
                status="blocked_by_policy",
                entries=[],
                output_ref=None,
                checksum=None,
                file_count=0,
                result={"reason": "policy_denied"},
            )
        record_audit_event(
            self._audit_sink,
            action_type="audit.export",
            resource_type="audit_export",
            resource_id=export_id,
            event_type="audit_export_started",
            outcome="dry_run" if request.dry_run else "completed",
            source_component="audit_exporter",
            trace_id=request.trace_id,
            payload={"dry_run": request.dry_run, "export_type": request.export_type},
        )
        entries = self._filtered_entries(request)
        if request.dry_run:
            return self._persist_record(
                request,
                export_id,
                status="dry_run",
                entries=entries,
                output_ref=str(Path(request.output_dir) / export_id),
                checksum=None,
                file_count=0,
                result={"planned": True, "entry_count": len(entries)},
            )
        try:
            output_dir = Path(request.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            payloads = [_export_entry(entry, request.redaction_mode) for entry in entries]
            checksum_payload = canonical_json({"entries": payloads, "export_id": export_id})
            checksum = sha256_text(checksum_payload)
            files = self._write_files(
                output_dir,
                export_id,
                request.export_type,
                payloads,
                checksum,
            )
            record = self._persist_record(
                request,
                export_id,
                status="completed",
                entries=entries,
                output_ref=str(output_dir),
                checksum=checksum,
                file_count=len(files),
                result={"files": [str(path) for path in files]},
            )
            record_audit_event(
                self._audit_sink,
                action_type="audit.export",
                resource_type="audit_export",
                resource_id=export_id,
                event_type="audit_export_completed",
                outcome="completed",
                source_component="audit_exporter",
                trace_id=request.trace_id,
                payload={"file_count": len(files), "entry_count": len(entries)},
            )
            return record
        except Exception as exc:
            record_audit_event(
                self._audit_sink,
                action_type="audit.export",
                resource_type="audit_export",
                resource_id=export_id,
                event_type="audit_export_failed",
                outcome="failed",
                source_component="audit_exporter",
                trace_id=request.trace_id,
                payload={"reason": type(exc).__name__},
            )
            return self._persist_record(
                request,
                export_id,
                status="failed",
                entries=entries,
                output_ref=None,
                checksum=None,
                file_count=0,
                result={"reason": type(exc).__name__},
            )

    def _allowed(self, request: AuditExportRequest) -> bool:
        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return True
        decision = authorize(
            PolicyRequest(
                request_id=f"audit.export-{request.audit_export_id or 'new'}",
                trace_id=request.trace_id,
                actor_id=request.created_by,
                workspace_id=None,
                action_type="audit.export",
                resource_type="audit_export",
                resource_id=request.audit_export_id,
                risk_level="medium",
                approval_present=False,
                requested_permissions=["audit.export"],
                security_scope=request.owner_scope,
                context={"dry_run": request.dry_run},
            )
        )
        return bool(getattr(decision, "allow", False))

    def _filtered_entries(self, request: AuditExportRequest) -> list[AuditEntry]:
        entries = self._repository.list_entries(
            trace_id=request.trace_id,
            resource_type=_optional_str(request.filters.get("resource_type")),
            action_type=_optional_str(request.filters.get("action_type")),
            from_sequence=request.from_sequence,
            to_sequence=request.to_sequence,
            limit=100_000,
            ascending=True,
        )
        return entries

    def _write_files(
        self,
        output_dir: Path,
        export_id: str,
        export_type: str,
        payloads: list[dict[str, Any]],
        checksum: str,
    ) -> list[Path]:
        files: list[Path] = []
        manifest = {
            "audit_export_id": export_id,
            "checksum": checksum,
            "entry_count": len(payloads),
            "created_at": datetime.now(UTC).isoformat(),
        }
        if export_type == "jsonl":
            data_file = output_dir / f"{export_id}.jsonl"
            data_file.write_text(
                "".join(f"{json.dumps(payload, sort_keys=True)}\n" for payload in payloads),
                encoding="utf-8",
            )
            files.append(data_file)
        elif export_type == "json":
            data_file = output_dir / f"{export_id}.json"
            data_file.write_text(json.dumps(payloads, sort_keys=True, indent=2), encoding="utf-8")
            files.append(data_file)
        manifest_file = output_dir / f"{export_id}.manifest.json"
        manifest_file.write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")
        files.append(manifest_file)
        return files

    def _persist_record(
        self,
        request: AuditExportRequest,
        export_id: str,
        *,
        status: str,
        entries: list[AuditEntry],
        output_ref: str | None,
        checksum: str | None,
        file_count: int,
        result: dict[str, Any],
    ) -> AuditExportRecord:
        record = AuditExportRecord(
            audit_export_id=export_id,
            trace_id=request.trace_id,
            export_type=request.export_type,
            status=status,  # type: ignore[arg-type]
            owner_scope=request.owner_scope,
            from_sequence=request.from_sequence,
            to_sequence=request.to_sequence,
            filters=request.filters,
            redaction_mode=request.redaction_mode,
            output_ref=output_ref,
            file_count=file_count,
            entry_count=len(entries),
            checksum=checksum,
            result=result,
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        return self._repository.save_export_record(record)


def _export_entry(entry: AuditEntry, redaction_mode: str) -> dict[str, Any]:
    data = entry.model_dump(mode="json")
    if redaction_mode == "metadata_only":
        return {
            "audit_entry_id": entry.audit_entry_id,
            "sequence_number": entry.sequence_number,
            "entry_hash": entry.entry_hash,
            "metadata": entry.metadata,
        }
    if redaction_mode == "exclude_sensitive":
        data.pop("canonical_payload", None)
        return data
    if "canonical_payload" in data and isinstance(data["canonical_payload"], dict):
        data["canonical_payload"], data["export_redaction_metadata"] = redact_audit_payload(
            data["canonical_payload"]
        )
    return data


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
