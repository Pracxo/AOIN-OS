"""Extension intake orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.extension_compatibility import ExtensionCompatibilityRequest
from aion_brain.contracts.extensions import ExtensionIntakeRequest, ExtensionIntakeRun
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.extensions.capabilities import CapabilityDeclarationService
from aion_brain.extensions.compatibility_gate import ExtensionCompatibilityGate
from aion_brain.extensions.dependencies import DependencyDeclarationService
from aion_brain.extensions.hash import hash_manifest
from aion_brain.extensions.install_plans import InstallPlanService
from aion_brain.extensions.manifest_validator import ManifestValidator
from aion_brain.extensions.packages import ExtensionPackageService
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository
from aion_brain.extensions.telemetry import emit_extension_telemetry


class ExtensionIntakeService:
    """Run dry-run or controlled metadata intake for extension manifests."""

    def __init__(
        self,
        repository: ExtensionRegistryRepository,
        policy_adapter: object,
        *,
        manifest_validator: ManifestValidator,
        package_service: ExtensionPackageService,
        dependency_service: DependencyDeclarationService,
        capability_service: CapabilityDeclarationService,
        compatibility_gate: ExtensionCompatibilityGate,
        install_plan_service: InstallPlanService,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        notification_router: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._manifest_validator = manifest_validator
        self._package_service = package_service
        self._dependency_service = dependency_service
        self._capability_service = capability_service
        self._compatibility_gate = compatibility_gate
        self._install_plan_service = install_plan_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._notification_router = notification_router
        self._settings = settings or get_settings()

    def intake(self, request: ExtensionIntakeRequest) -> ExtensionIntakeRun:
        """Validate and optionally persist extension package metadata."""

        authorize_extension_action(
            self._policy_adapter,
            "extension.intake",
            request.owner_scope,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="extension_intake",
            risk_level="medium",
            context={"mode": request.mode, "extension_key": request.manifest.extension_key},
        )
        intake_id = request.extension_intake_id or f"extension-intake-{uuid4().hex}"
        emit_extension_telemetry(
            self._telemetry_service,
            event_type="extension_intake_started",
            node_type="extension",
            node_id=intake_id,
            scope=request.owner_scope,
            intensity=0.5,
            payload={"mode": request.mode},
        )
        validation = self._manifest_validator.validate(request.manifest)
        package = self._package_service.build_package(
            request,
            status="proposed",
            compatibility_status="unknown",
            review_status="not_reviewed",
        )
        capabilities = self._capability_service.from_package(package)
        dependencies = self._dependency_service.from_package(package)
        capability_result = self._capability_service.validate_declarations(capabilities)
        dependency_result = self._dependency_service.check_dependencies(package, dependencies)
        blockers = [
            *validation["blockers"],
            *capability_result["blockers"],
            *dependency_result["blockers"],
        ]
        warnings = [
            *validation["warnings"],
            *capability_result["warnings"],
            *dependency_result["warnings"],
        ]
        saved_package = None
        compatibility_status = "unknown"
        install_plan_created = False
        if request.mode == "controlled" and not blockers:
            saved_package = self._package_service.save_package(package)
            self._capability_service.persist_declarations(saved_package, capabilities)
            self._dependency_service.persist_declarations(saved_package, dependencies)
            if request.run_compatibility:
                compatibility = self._compatibility_gate.check_package(
                    saved_package,
                    ExtensionCompatibilityRequest(
                        trace_id=request.trace_id,
                        extension_package_id=saved_package.extension_package_id,
                        mode=request.mode,
                        owner_scope=request.owner_scope,
                        metadata={"source": "extension_intake"},
                        created_by=request.created_by,
                    ),
                )
                compatibility_status = compatibility.status
                blockers.extend(compatibility.blockers)
                warnings.extend(compatibility.warnings)
                saved_package = self._repository.get_package(saved_package.extension_package_id)
            if (
                request.create_install_plan
                and bool(getattr(self._settings, "extension_install_plans_enabled", True))
                and saved_package is not None
            ):
                self._install_plan_service.create_plan(
                    saved_package,
                    scope=request.owner_scope,
                    created_by=request.created_by,
                )
                install_plan_created = True
        else:
            compatibility_status = "blocked" if blockers else "unknown"
        status = _intake_status(request.mode, blockers, warnings)
        run = ExtensionIntakeRun(
            extension_intake_id=intake_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            extension_package=saved_package,
            manifest_hash=hash_manifest(request.manifest.model_dump(mode="json")),
            validation_status=validation["status"],
            compatibility_status=cast(Any, compatibility_status),
            review_required=bool(
                request.mode == "controlled" and saved_package is not None and not blockers
            ),
            install_plan_created=install_plan_created,
            findings=[*validation["findings"]],
            blockers=blockers,
            warnings=warnings,
            result={
                "metadata_only": True,
                "dry_run_persisted_package": False,
                "package_persisted": saved_package is not None,
                "capability_count": len(capabilities),
                "dependency_count": len(dependencies),
            },
            metadata={**request.metadata, "source_mutated": False},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        saved_run = self._repository.save_intake_run(run)
        self._record_audit(request, saved_run)
        self._maybe_notify(request, saved_run)
        emit_extension_telemetry(
            self._telemetry_service,
            event_type="extension_manifest_validated",
            node_type="extension_manifest",
            node_id=saved_run.extension_intake_id,
            scope=saved_run.owner_scope,
            intensity=0.4,
            payload={"status": saved_run.validation_status},
        )
        emit_extension_telemetry(
            self._telemetry_service,
            event_type="extension_intake_completed",
            node_type="extension",
            node_id=saved_run.extension_intake_id,
            scope=saved_run.owner_scope,
            intensity=0.9 if blockers else 0.6,
            payload={"status": saved_run.status, "package_persisted": saved_package is not None},
        )
        return saved_run

    def get_intake_run(
        self,
        extension_intake_id: str,
        scope: list[str],
    ) -> ExtensionIntakeRun | None:
        authorize_extension_action(
            self._policy_adapter,
            "extension.query",
            scope,
            resource_type="extension_intake",
            resource_id=extension_intake_id,
            risk_level="low",
        )
        return self._repository.get_intake_run(extension_intake_id)

    def _record_audit(self, request: ExtensionIntakeRequest, run: ExtensionIntakeRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="extension.intake",
            resource_type="extension_intake",
            resource_id=run.extension_intake_id,
            event_type="extension_intake_completed",
            outcome="completed" if run.status != "failed" else "failed",
            source_component="extension_registry",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="medium",
            payload={
                "status": run.status,
                "mode": run.mode,
                "package_persisted": run.extension_package is not None,
            },
        )

    def _maybe_notify(self, request: ExtensionIntakeRequest, run: ExtensionIntakeRun) -> None:
        if not (
            request.create_notifications
            or bool(getattr(self._settings, "extension_create_notifications_default", False))
        ):
            return
        publish = getattr(self._notification_router, "publish", None)
        if not callable(publish):
            return
        try:
            publish(
                NotificationPublishRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    topic_key="generic.info",
                    severity="medium" if run.blockers else "info",
                    title="Extension intake completed",
                    message=f"Extension intake {run.extension_intake_id} completed.",
                    source_type="generic",
                    source_id=run.extension_intake_id,
                    target_type="operator",
                    target_id="operator",
                    owner_scope=run.owner_scope,
                    refs=[run.extension_intake_id],
                    metadata={"status": run.status, "metadata_only": True},
                    created_by=request.created_by,
                )
            )
        except Exception:
            return


def _intake_status(
    mode: str,
    blockers: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    if blockers:
        return "failed"
    if mode == "dry_run":
        return "dry_run"
    if warnings:
        return "warning"
    return "completed"


__all__ = ["ExtensionIntakeService"]
