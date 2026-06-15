"""Restore dry-run and guarded apply service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.backups.exporter import (
    _decision_denied,
    _decision_reason,
    _jsonable,
    _optional_decision,
)
from aion_brain.backups.redaction import strip_sensitive_metadata
from aion_brain.backups.repository import BackupRepository
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.backups import RestoreJob, RestoreRequest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class RestoreService:
    """Create restore jobs without direct database restore side effects by default."""

    def __init__(
        self,
        backup_repository: BackupRepository,
        policy_adapter: PolicyAdapter,
        *,
        autonomy_governor: object | None = None,
        risk_engine: object | None = None,
        approval_service: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = backup_repository
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def restore(self, request: RestoreRequest) -> RestoreJob:
        """Create a dry-run or guarded restore job."""
        preview = self._repository.get_restore_preview(request.restore_preview_id)
        if preview is None:
            raise AIONNotFoundException("restore_preview_not_found")
        action = "backup.restore.apply" if request.mode == "apply" else "backup.restore.preview"
        risk_level = "high" if request.mode == "apply" else "low"
        self._authorize(
            action,
            request.owner_scope,
            actor_id=request.actor_id or request.created_by,
            workspace_id=request.workspace_id,
            resource_id=request.restore_preview_id,
            risk_level=risk_level,
            approval_present=request.approval_present,
        )
        created_at = datetime.now(UTC)
        restore_job_id = request.restore_job_id or f"restore-job-{uuid4().hex}"
        self._emit(
            "restore_started",
            "restore",
            restore_job_id,
            request.owner_scope,
            0.5,
            {"mode": request.mode},
        )
        if request.mode == "dry_run":
            job = RestoreJob(
                restore_job_id=restore_job_id,
                restore_preview_id=request.restore_preview_id,
                backup_job_id=preview.backup_job_id,
                trace_id=preview.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                status="dry_run",
                mode="dry_run",
                result=strip_sensitive_metadata(
                    {
                        "records_seen": preview.records_seen,
                        "records_restorable": preview.records_restorable,
                        "conflict_count": preview.conflict_count,
                        "writes_performed": 0,
                    }
                ),
                created_by=request.created_by,
                created_at=created_at,
                completed_at=datetime.now(UTC),
            )
            return self._save_and_emit(job, request.owner_scope)
        if not self._settings.backup_restore_apply_enabled:
            job = RestoreJob(
                restore_job_id=restore_job_id,
                restore_preview_id=request.restore_preview_id,
                backup_job_id=preview.backup_job_id,
                trace_id=preview.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                status="unsupported",
                mode="apply",
                result={"reason": "restore_apply_disabled_by_default", "writes_performed": 0},
                created_by=request.created_by,
                created_at=created_at,
                completed_at=datetime.now(UTC),
            )
            self._emit(
                "restore_blocked",
                "restore",
                restore_job_id,
                request.owner_scope,
                0.95,
                {"reason": "restore_apply_disabled_by_default"},
            )
            return self._repository.save_restore_job(job)
        autonomy = _optional_decision(
            self._autonomy_governor,
            "decide",
            action_type="backup.restore.apply",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
        )
        if _decision_denied(autonomy):
            return self._save_and_emit(
                self._blocked_job(
                    request,
                    restore_job_id,
                    preview.backup_job_id,
                    preview.trace_id,
                    "blocked_by_autonomy",
                    {"reason": _decision_reason(autonomy, "autonomy_denied")},
                    created_at,
                ),
                request.owner_scope,
            )
        risk = _optional_decision(
            self._risk_engine,
            "assess",
            action_type="backup.restore.apply",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
        )
        approval = _optional_decision(
            self._approval_service,
            "verify",
            action_type="backup.restore.apply",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
        )
        job = RestoreJob(
            restore_job_id=restore_job_id,
            restore_preview_id=request.restore_preview_id,
            backup_job_id=preview.backup_job_id,
            trace_id=preview.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="completed",
            mode="apply",
            approval_request_id=_id_from(approval),
            risk_assessment_id=_id_from(risk),
            autonomy_decision_id=_id_from(autonomy),
            result=strip_sensitive_metadata(
                {
                    "reason": "restore_apply_reserved_for_application_writers",
                    "conflict_strategy": preview.plan.get("conflict_strategy", "skip_conflicts"),
                    "writes_performed": 0,
                    "risk": _jsonable(risk),
                    "approval": _jsonable(approval),
                }
            ),
            created_by=request.created_by,
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )
        return self._save_and_emit(job, request.owner_scope)

    def _blocked_job(
        self,
        request: RestoreRequest,
        restore_job_id: str,
        backup_job_id: str | None,
        trace_id: str | None,
        status: str,
        result: dict[str, Any],
        created_at: datetime,
    ) -> RestoreJob:
        return RestoreJob(
            restore_job_id=restore_job_id,
            restore_preview_id=request.restore_preview_id,
            backup_job_id=backup_job_id,
            trace_id=trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            mode=request.mode,
            result=strip_sensitive_metadata(result),
            created_by=request.created_by,
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )

    def _save_and_emit(self, job: RestoreJob, scope: list[str]) -> RestoreJob:
        saved = self._repository.save_restore_job(job)
        self._emit(
            "restore_completed",
            "restore",
            saved.restore_job_id,
            scope,
            0.8 if saved.status not in {"failed", "blocked_by_autonomy"} else 1.0,
            {"status": saved.status, "mode": saved.mode},
        )
        return saved

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None,
        workspace_id: str | None,
        resource_id: str | None,
        risk_level: str,
        approval_present: bool,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="restore_job",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[action_type],
                security_scope=scope,
                context={"mode": "restore"},
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


def _id_from(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("approval_request_id", "risk_assessment_id", "autonomy_decision_id", "id"):
            if value.get(key) is not None:
                return str(value[key])
    for attr in ("approval_request_id", "risk_assessment_id", "autonomy_decision_id", "id"):
        item = getattr(value, attr, None)
        if item is not None:
            return str(item)
    return None
