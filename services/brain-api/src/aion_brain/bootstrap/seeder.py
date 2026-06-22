"""Idempotent local seed bundle executor."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.bootstrap.policy import authorize_bootstrap_action
from aion_brain.bootstrap.redaction import safe_summary
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.bootstrap.seed_bundles import SeedBundleService
from aion_brain.bootstrap.telemetry import emit_bootstrap_telemetry
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.bootstrap import SeedBundle, SeedExecutionRecord, SeedExecutionRequest


class SeedExecutor:
    """Execute local seed bundles without external side effects."""

    def __init__(
        self,
        repository: BootstrapRepository,
        bundle_service: SeedBundleService,
        policy_adapter: object,
        *,
        service_dependencies: dict[str, object] | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._bundle_service = bundle_service
        self._policy_adapter = policy_adapter
        self._service_dependencies = service_dependencies or {}
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings or get_settings()

    def set_service_dependency(self, service_key: str, service: object) -> None:
        """Register or replace a local metadata seed dependency."""
        self._service_dependencies[service_key] = service

    def execute(self, request: SeedExecutionRequest) -> SeedExecutionRecord:
        """Execute one seed bundle idempotently."""
        if not self._settings.seed_bundles_enabled:
            return self._blocked_record(request, "seed_bundles_disabled")
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.seed.execute",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="seed_bundle",
            resource_id=request.seed_bundle_key,
            risk_level="medium",
            context={
                "mode": request.mode,
                "dry_run": request.mode == "dry_run",
                "external_calls": False,
                "safe_local_defaults": True,
                **request.metadata,
            },
        )
        bundle = self._bundle_service.get_bundle(request.seed_bundle_key, request.owner_scope)
        if bundle is None:
            return self._failed_record(request, "seed_bundle_not_found")
        if request.mode == "controlled" and not self._controlled_allowed(request):
            return self._blocked_record(request, "controlled_seed_disabled", bundle)
        seed_execution_id = request.seed_execution_id or f"seed-execution-{uuid4().hex}"
        self._emit(
            "seed_execution_started",
            "seed_execution",
            seed_execution_id,
            request.owner_scope,
            0.5,
            {"seed_bundle_key": request.seed_bundle_key, "mode": request.mode},
        )
        attempted = len(bundle.seed_steps)
        completed = 0
        skipped = 0
        failed = 0
        created_refs: list[str] = []
        skipped_refs: list[str] = []
        failures: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        for step in bundle.seed_steps:
            idempotency_key = str(step.get("idempotency_key", step.get("step_key", "seed")))
            resource_ref = f"aion://seed_execution/{bundle.seed_bundle_key}/{idempotency_key}"
            if (
                self._already_completed(bundle.seed_bundle_key, idempotency_key)
                and not request.force
            ):
                skipped += 1
                skipped_refs.append(resource_ref)
                continue
            if step.get("external_calls") is True or step.get("external_call") is True:
                failed += 1
                failures.append({"step": idempotency_key, "reason": "external_step_blocked"})
                continue
            if request.mode == "dry_run":
                skipped += 1
                skipped_refs.append(resource_ref)
                continue
            try:
                result = self._execute_step(step, request, bundle)
                if result.get("status") == "skipped":
                    skipped += 1
                    skipped_refs.append(resource_ref)
                else:
                    completed += 1
                    created_refs.append(resource_ref)
            except Exception as exc:
                failed += 1
                failures.append({"step": idempotency_key, "reason": exc.__class__.__name__})
        status = "dry_run" if request.mode == "dry_run" else "completed"
        if failed:
            status = "failed"
        elif skipped and completed:
            status = "warning"
        record = SeedExecutionRecord(
            seed_execution_id=seed_execution_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            seed_bundle_id=bundle.seed_bundle_id,
            seed_bundle_key=bundle.seed_bundle_key,
            status=status,  # type: ignore[arg-type]
            mode=request.mode,
            owner_scope=request.owner_scope,
            steps_attempted=attempted,
            steps_completed=completed,
            steps_skipped=skipped,
            steps_failed=failed,
            created_resource_refs=created_refs,
            skipped_resource_refs=skipped_refs,
            failures=failures,
            warnings=warnings,
            result={
                "dry_run": request.mode == "dry_run",
                "external_calls": False,
                "package_install": False,
                "source_mutation": False,
            },
            metadata=safe_summary(request.metadata),
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_seed_execution(record)
        self._record_audit(saved)
        self._emit(
            "seed_execution_completed",
            "seed_execution",
            saved.seed_execution_id,
            saved.owner_scope,
            0.8 if saved.status in {"completed", "dry_run"} else 1.0,
            {"status": saved.status, "seed_bundle_key": saved.seed_bundle_key},
        )
        return saved

    def _execute_step(
        self,
        step: dict[str, Any],
        request: SeedExecutionRequest,
        bundle: SeedBundle,
    ) -> dict[str, Any]:
        service_key = str(step.get("service_key", ""))
        service = self._service_dependencies.get(service_key)
        if service is None:
            return {"status": "completed", "metadata_only": True}
        for method_name in (
            "seed_default_scenarios",
            "seed_default_fixture_packs",
            "seed_default_profiles",
            "seed_default_bundles",
            "seed_defaults",
            "seed_default_rules",
            "seed_default_policies",
            "seed_default_topics",
        ):
            method = getattr(service, method_name, None)
            if callable(method):
                return _safe_call_seed(method, request, bundle)
        return {"status": "completed", "metadata_only": True}

    def _already_completed(self, seed_bundle_key: str, idempotency_key: str) -> bool:
        records = self._repository.list_seed_executions(
            status="completed",
            seed_bundle_key=seed_bundle_key,
            limit=100,
        )
        marker = f"/{idempotency_key}"
        return any(
            any(ref.endswith(marker) for ref in record.created_resource_refs) for record in records
        )

    def _controlled_allowed(self, request: SeedExecutionRequest) -> bool:
        return bool(
            self._settings.bootstrap_controlled_mode_enabled
            or request.metadata.get("allow_local_defaults") is True
        )

    def _blocked_record(
        self,
        request: SeedExecutionRequest,
        reason: str,
        bundle: SeedBundle | None = None,
    ) -> SeedExecutionRecord:
        now = datetime.now(UTC)
        return self._repository.save_seed_execution(
            SeedExecutionRecord(
                seed_execution_id=request.seed_execution_id or f"seed-execution-{uuid4().hex}",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                seed_bundle_id=getattr(bundle, "seed_bundle_id", request.seed_bundle_key),
                seed_bundle_key=request.seed_bundle_key,
                status="blocked_by_policy",
                mode=request.mode,
                owner_scope=request.owner_scope,
                steps_attempted=0,
                steps_completed=0,
                steps_skipped=0,
                steps_failed=0,
                created_resource_refs=[],
                skipped_resource_refs=[],
                failures=[{"reason": reason}],
                warnings=[],
                result={"blocked": True, "reason": reason},
                metadata=safe_summary(request.metadata),
                created_by=request.created_by,
                created_at=now,
                completed_at=now,
            )
        )

    def _failed_record(self, request: SeedExecutionRequest, reason: str) -> SeedExecutionRecord:
        now = datetime.now(UTC)
        return self._repository.save_seed_execution(
            SeedExecutionRecord(
                seed_execution_id=request.seed_execution_id or f"seed-execution-{uuid4().hex}",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                seed_bundle_id=request.seed_bundle_key,
                seed_bundle_key=request.seed_bundle_key,
                status="failed",
                mode=request.mode,
                owner_scope=request.owner_scope,
                steps_attempted=0,
                steps_completed=0,
                steps_skipped=0,
                steps_failed=1,
                created_resource_refs=[],
                skipped_resource_refs=[],
                failures=[{"reason": reason}],
                warnings=[],
                result={"failed": True, "reason": reason},
                metadata=safe_summary(request.metadata),
                created_by=request.created_by,
                created_at=now,
                completed_at=now,
            )
        )

    def _record_audit(self, record: SeedExecutionRecord) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="bootstrap.seed.execute",
            resource_type="seed_execution",
            resource_id=record.seed_execution_id,
            event_type="seed_execution_created",
            outcome=record.status,
            source_component="bootstrap_seed_executor",
            trace_id=record.trace_id,
            actor_id=record.created_by or record.actor_id,
            workspace_id=record.workspace_id,
            risk_level="medium",
            payload={"seed_bundle_key": record.seed_bundle_key, "status": record.status},
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        scope: list[str],
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_bootstrap_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            intensity=intensity,
            payload=payload,
        )


def _safe_call_seed(
    method: Callable[..., object], request: SeedExecutionRequest, bundle: SeedBundle
) -> dict[str, Any]:
    for kwargs in (
        {"scope": request.owner_scope, "dry_run": False, "created_by": request.created_by},
        {"scope": request.owner_scope, "created_by": request.created_by},
        {"dry_run": False, "created_by": request.created_by},
        {"created_by": request.created_by},
        {},
    ):
        try:
            result = method(**kwargs)
            return result if isinstance(result, dict) else {"status": "completed"}
        except TypeError:
            continue
    return {"status": "completed", "seed_bundle_key": bundle.seed_bundle_key}


__all__ = ["SeedExecutor"]
