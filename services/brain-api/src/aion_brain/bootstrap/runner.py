"""First-run bootstrap runner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.bootstrap.doctor import SetupDoctor
from aion_brain.bootstrap.policy import authorize_bootstrap_action
from aion_brain.bootstrap.profiles import BootstrapProfileService
from aion_brain.bootstrap.redaction import safe_summary
from aion_brain.bootstrap.reports import SetupReportService
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.bootstrap.seed_bundles import SeedBundleService
from aion_brain.bootstrap.seeder import SeedExecutor
from aion_brain.bootstrap.telemetry import emit_bootstrap_telemetry
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.bootstrap import (
    BootstrapRun,
    BootstrapRunRequest,
    SeedExecutionRequest,
)
from aion_brain.contracts.golden_path import GoldenPathRunRequest
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.contracts.operator import OperatorActionItem
from aion_brain.contracts.setup_doctor import SetupDoctorRequest, SetupFinding


class BootstrapRunner:
    """Run local first-run bootstrap without provisioning side effects."""

    def __init__(
        self,
        repository: BootstrapRepository,
        profile_service: BootstrapProfileService,
        bundle_service: SeedBundleService,
        seed_executor: SeedExecutor,
        setup_doctor: SetupDoctor,
        report_service: SetupReportService,
        policy_adapter: object,
        *,
        golden_path_runner: object | None = None,
        release_smoke: object | None = None,
        autonomy_governor: object | None = None,
        notification_router: object | None = None,
        operator_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._profile_service = profile_service
        self._bundle_service = bundle_service
        self._seed_executor = seed_executor
        self._setup_doctor = setup_doctor
        self._report_service = report_service
        self._policy_adapter = policy_adapter
        self._golden_path_runner = golden_path_runner
        self._release_smoke = release_smoke
        self._autonomy_governor = autonomy_governor
        self._notification_router = notification_router
        self._operator_repository = operator_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings or get_settings()

    def run(self, request: BootstrapRunRequest) -> BootstrapRun:
        """Run local bootstrap."""
        if not self._settings.bootstrap_enabled:
            return self._blocked_run(request, "bootstrap_disabled")
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.run",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="bootstrap_run",
            resource_id=request.bootstrap_run_id,
            risk_level="medium",
            context=_run_context(request),
        )
        if request.mode == "controlled" and not self._controlled_allowed(request):
            return self._blocked_run(request, "controlled_bootstrap_disabled")

        run_id = request.bootstrap_run_id or f"bootstrap-run-{uuid4().hex}"
        trace_id = request.trace_id or f"trace-bootstrap-{uuid4().hex}"
        created_at = datetime.now(UTC)
        self._emit(
            "bootstrap_run_started",
            "bootstrap",
            run_id,
            request.owner_scope,
            0.6,
            {"mode": request.mode, "profile_key": request.profile_key},
        )
        profile = self._profile_service.get_profile(request.profile_key, request.owner_scope)
        if request.seed_defaults:
            self._profile_service.seed_default_profiles(
                request.owner_scope,
                dry_run=request.mode == "dry_run",
                created_by=request.created_by,
            )
            self._bundle_service.seed_default_bundles(
                request.owner_scope,
                dry_run=request.mode == "dry_run",
                created_by=request.created_by,
            )
        seed_executions = []
        warnings: list[dict[str, Any]] = []
        if profile is not None and request.seed_defaults:
            for seed_bundle_key in profile.seed_bundle_keys:
                seed_executions.append(
                    self._seed_executor.execute(
                        SeedExecutionRequest(
                            trace_id=trace_id,
                            actor_id=request.actor_id,
                            workspace_id=request.workspace_id,
                            seed_bundle_key=seed_bundle_key,
                            mode=request.mode,
                            owner_scope=request.owner_scope,
                            metadata={
                                "allow_local_defaults": request.metadata.get(
                                    "allow_local_defaults", False
                                ),
                                "bootstrap_run_id": run_id,
                            },
                            created_by=request.created_by,
                        )
                    )
                )

        golden_path_run_id = None
        if request.run_golden_path and self._golden_path_runner is not None:
            run_method = getattr(self._golden_path_runner, "run", None)
            if callable(run_method):
                try:
                    golden = run_method(
                        GoldenPathRunRequest(
                            trace_id=trace_id,
                            actor_id=request.actor_id,
                            workspace_id=request.workspace_id,
                            mode="dry_run",
                            owner_scope=request.owner_scope,
                            run_all_defaults=True,
                            create_notifications=False,
                            create_operator_items=False,
                            include_release_smoke=False,
                            metadata={"source": "bootstrap", "external_calls": False},
                            created_by=request.created_by,
                        )
                    )
                    golden_path_run_id = getattr(golden, "golden_path_run_id", None)
                except Exception as exc:
                    warnings.append(
                        {
                            "check": "golden_path",
                            "reason": exc.__class__.__name__,
                            "message": "optional golden path dry-run failed",
                        }
                    )

        release_smoke_ref = None
        if request.run_release_smoke and self._release_smoke is not None:
            smoke = getattr(self._release_smoke, "run", None)
            if callable(smoke):
                try:
                    result = smoke(request.owner_scope, created_by=request.created_by)
                    if isinstance(result, dict):
                        release_smoke_ref = str(result.get("release_smoke_id", "release_smoke"))
                except Exception as exc:
                    warnings.append(
                        {
                            "check": "release_smoke",
                            "reason": exc.__class__.__name__,
                            "message": "optional release smoke failed",
                        }
                    )

        doctor_result = None
        if request.run_setup_doctor:
            doctor_result = self._setup_doctor.run(
                SetupDoctorRequest(
                    trace_id=trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    owner_scope=request.owner_scope,
                    include_golden_path=request.run_golden_path,
                    include_release_smoke=request.run_release_smoke,
                    create_findings=True,
                    create_notifications=request.create_notifications,
                    metadata={"bootstrap_run_id": run_id},
                    created_by=request.created_by,
                )
            )
        setup_findings = list(doctor_result.findings) if doctor_result is not None else []
        report = (
            self._report_service.create_report(
                doctor_result,
                bootstrap_run_id=run_id,
                created_by=request.created_by,
                trace_id=trace_id,
            )
            if doctor_result is not None
            else None
        )
        readiness_score = doctor_result.readiness_score if doctor_result is not None else 0.0
        local_ready = bool(doctor_result.local_ready if doctor_result is not None else False)
        critical_findings = [item for item in setup_findings if item.severity == "critical"]
        status = "dry_run" if request.mode == "dry_run" and not critical_findings else "completed"
        if critical_findings:
            status = "failed"
        elif (
            doctor_result is not None
            and doctor_result.status == "warning"
            and request.mode != "dry_run"
        ):
            status = "warning"
        run = BootstrapRun(
            bootstrap_run_id=run_id,
            trace_id=trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            bootstrap_profile=profile,
            status=status,  # type: ignore[arg-type]
            mode=request.mode,
            owner_scope=request.owner_scope,
            checks_run=doctor_result.checks_run if doctor_result is not None else [],
            seed_executions=seed_executions,
            setup_findings=setup_findings,
            golden_path_run_id=golden_path_run_id,
            release_smoke_ref=release_smoke_ref,
            readiness_score=readiness_score,
            local_ready=local_ready,
            warnings=warnings,
            failures=[
                {"setup_finding_id": item.setup_finding_id, "severity": item.severity}
                for item in critical_findings
            ],
            result={
                "setup_report_id": getattr(report, "setup_report_id", None),
                "external_calls": False,
                "package_install": False,
                "production_provisioning": False,
                "source_mutation": False,
            },
            metadata=safe_summary(request.metadata),
            created_by=request.created_by,
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_run(run)
        self._record_audit(saved)
        self._maybe_notify(saved, request)
        self._maybe_operator_item(saved, request, setup_findings)
        self._emit(
            "bootstrap_run_completed",
            "bootstrap",
            saved.bootstrap_run_id,
            saved.owner_scope,
            saved.readiness_score,
            {"status": saved.status, "local_ready": saved.local_ready},
        )
        return saved

    def get_run(self, bootstrap_run_id: str, scope: list[str]) -> BootstrapRun | None:
        """Return one bootstrap run."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.run.read",
            scope,
            resource_type="bootstrap_run",
            resource_id=bootstrap_run_id,
        )
        return self._repository.get_run(bootstrap_run_id)

    def list_runs(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        profile_key: str | None = None,
        limit: int = 50,
    ) -> list[BootstrapRun]:
        """List bootstrap runs."""
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.run.read",
            scope,
            resource_type="bootstrap_run",
        )
        return self._repository.list_runs(status=status, profile_key=profile_key, limit=limit)

    def _controlled_allowed(self, request: BootstrapRunRequest) -> bool:
        return bool(
            self._settings.bootstrap_controlled_mode_enabled
            or request.metadata.get("allow_local_defaults") is True
        )

    def _blocked_run(self, request: BootstrapRunRequest, reason: str) -> BootstrapRun:
        now = datetime.now(UTC)
        run = BootstrapRun(
            bootstrap_run_id=request.bootstrap_run_id or f"bootstrap-run-{uuid4().hex}",
            trace_id=request.trace_id or f"trace-bootstrap-{uuid4().hex}",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            bootstrap_profile=None,
            status="blocked_by_policy",
            mode=request.mode,
            owner_scope=request.owner_scope,
            checks_run=[],
            seed_executions=[],
            setup_findings=[],
            golden_path_run_id=None,
            release_smoke_ref=None,
            readiness_score=0.0,
            local_ready=False,
            warnings=[],
            failures=[{"reason": reason}],
            result={"blocked": True, "reason": reason},
            metadata=safe_summary(request.metadata),
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        return self._repository.save_run(run)

    def _record_audit(self, run: BootstrapRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="bootstrap.run",
            resource_type="bootstrap_run",
            resource_id=run.bootstrap_run_id,
            event_type="bootstrap_run_created",
            outcome=run.status,
            source_component="bootstrap_runner",
            trace_id=run.trace_id,
            actor_id=run.created_by or run.actor_id,
            workspace_id=run.workspace_id,
            risk_level="medium",
            payload={"status": run.status, "readiness_score": run.readiness_score},
        )

    def _maybe_notify(self, run: BootstrapRun, request: BootstrapRunRequest) -> None:
        if not (
            request.create_notifications or self._settings.bootstrap_create_notifications_default
        ):
            return
        publish = getattr(self._notification_router, "publish", None)
        if not callable(publish):
            return
        try:
            publish(
                NotificationPublishRequest(
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    topic_key="bootstrap.local_setup",
                    title="Bootstrap run completed.",
                    message=f"Bootstrap run {run.bootstrap_run_id} completed.",
                    severity="info" if run.local_ready else "medium",
                    owner_scope=run.owner_scope,
                    source_type="generic",
                    source_id=run.bootstrap_run_id,
                    target_type="operator",
                    target_id="operator",
                    refs=[run.bootstrap_run_id],
                    metadata={"status": run.status, "readiness_score": run.readiness_score},
                    created_by=request.created_by,
                )
            )
        except Exception:
            return

    def _maybe_operator_item(
        self,
        run: BootstrapRun,
        request: BootstrapRunRequest,
        findings: list[SetupFinding],
    ) -> None:
        if not (
            request.create_operator_items or self._settings.bootstrap_create_operator_items_default
        ):
            return
        save = getattr(self._operator_repository, "save_action_item", None)
        if not callable(save):
            return
        critical = [item for item in findings if item.severity == "critical"]
        if not critical:
            return
        try:
            save(
                OperatorActionItem(
                    action_item_id=f"operator-action-bootstrap-{uuid4().hex}",
                    title="Bootstrap setup has critical findings.",
                    description="A local setup report contains critical findings.",
                    category="operator",
                    severity="critical",
                    status="open",
                    source_type="setup_finding",
                    source_id=critical[0].setup_finding_id,
                    trace_id=run.trace_id,
                    owner_scope=run.owner_scope,
                    recommended_action="run_setup_doctor",
                    runbook_ref="docs/operations/bootstrap.md",
                    metadata={"bootstrap_run_id": run.bootstrap_run_id},
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return

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


def _run_context(request: BootstrapRunRequest) -> dict[str, Any]:
    return {
        "mode": request.mode,
        "dry_run": request.mode == "dry_run",
        "external_calls": False,
        "package_install": False,
        "production_provisioning": False,
        "enable_external_features": False,
        **request.metadata,
    }


__all__ = ["BootstrapRunner"]
