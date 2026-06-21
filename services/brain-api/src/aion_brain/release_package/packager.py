"""Local release package assembly service."""

from __future__ import annotations

import builtins
import json
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import (
    AIONNotFoundException,
    AIONPolicyDeniedException,
    AIONUnsupportedOperationException,
)
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.release_package import (
    ReleaseHandoffReport,
    ReleasePackage,
    ReleasePackageFile,
    ReleasePackageManifest,
    ReleasePackageRequest,
    ReleasePackageValidation,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.release_package.checksums import root_checksum, sha256_bytes
from aion_brain.release_package.handoff import ReleaseHandoffService
from aion_brain.release_package.repository import ReleasePackageRepository
from aion_brain.release_package.sbom import SBOMPlaceholderService
from aion_brain.release_package.source_manifest import SourceManifestService
from aion_brain.release_package.validator import ReleasePackageValidator
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ReleasePackager:
    """Assemble deterministic local AION release packages."""

    def __init__(
        self,
        repository: ReleasePackageRepository,
        policy_adapter: PolicyAdapter,
        *,
        version_manifest_service: object | None = None,
        contract_export_service: object | None = None,
        policy_bundle_service: object | None = None,
        migration_baseline_service: object | None = None,
        release_baseline_service: object | None = None,
        freeze_gate_service: object | None = None,
        hardening_gate_service: object | None = None,
        compatibility_matrix_service: object | None = None,
        release_artifact_service: object | None = None,
        source_manifest_service: SourceManifestService | None = None,
        sbom_service: SBOMPlaceholderService | None = None,
        validator: ReleasePackageValidator | None = None,
        handoff_service: ReleaseHandoffService | None = None,
        contract_registry_repository: object | None = None,
        contract_registry_report_service: object | None = None,
        extension_registry_repository: object | None = None,
        module_binding_repository: object | None = None,
        conformance_repository: object | None = None,
        telemetry_service: object | None = None,
        root_dir: Path | None = None,
        settings: Settings | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._version_manifest_service = version_manifest_service
        self._contract_export_service = contract_export_service
        self._policy_bundle_service = policy_bundle_service
        self._migration_baseline_service = migration_baseline_service
        self._release_baseline_service = release_baseline_service
        self._freeze_gate_service = freeze_gate_service
        self._hardening_gate_service = hardening_gate_service
        self._compatibility_matrix_service = compatibility_matrix_service
        self._release_artifact_service = release_artifact_service
        self._settings = settings or get_settings()
        self._root_dir = root_dir or Path(__file__).parents[5]
        self._source_manifest_service = source_manifest_service or SourceManifestService(
            max_file_size_mb=self._settings.release_package_max_file_size_mb
        )
        self._sbom_service = sbom_service or SBOMPlaceholderService(self._root_dir)
        self._validator = validator or ReleasePackageValidator(
            max_file_size_mb=self._settings.release_package_max_file_size_mb
        )
        self._handoff_service = handoff_service or ReleaseHandoffService()
        self._contract_registry_repository = contract_registry_repository
        self._contract_registry_report_service = contract_registry_report_service
        self._extension_registry_repository = extension_registry_repository
        self._module_binding_repository = module_binding_repository
        self._conformance_repository = conformance_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def set_contract_registry_services(
        self,
        *,
        repository: object | None = None,
        report_service: object | None = None,
    ) -> None:
        """Attach Contract Registry summaries after kernel assembly."""

        self._contract_registry_repository = repository
        self._contract_registry_report_service = report_service

    def set_extension_registry_services(
        self,
        *,
        repository: object | None = None,
    ) -> None:
        """Attach Extension Registry summaries after kernel assembly."""

        self._extension_registry_repository = repository

    def set_module_binding_registry(
        self,
        repository: object | None = None,
    ) -> None:
        """Attach module binding summaries after kernel assembly."""

        self._module_binding_repository = repository

    def set_conformance_repository(self, repository: object | None = None) -> None:
        """Attach capability conformance summaries after kernel assembly."""

        self._conformance_repository = repository

    def package(
        self,
        request: ReleasePackageRequest,
        *,
        app: object | None = None,
    ) -> ReleasePackage:
        """Create or dry-run a local release package."""
        if not self._settings.release_packaging_enabled:
            raise AIONUnsupportedOperationException("release_packaging_disabled")
        self._authorize(
            "release.package.create",
            request.owner_scope,
            actor_id=request.created_by,
            risk_level="medium",
            context={"version": request.version, "dry_run": request.dry_run},
        )
        release_package_id = request.release_package_id or f"release-package-{uuid4().hex}"
        package_name = f"aion-{request.version}-local-release"
        created_at = datetime.now(UTC)
        self._emit(
            "release_package_started",
            release_package_id,
            request.owner_scope,
            0.5,
            {"version": request.version, "dry_run": request.dry_run},
        )
        reports = self._collect_reports(request, app)
        source_manifest = reports.get("source_manifest")
        files = self._build_files(release_package_id, source_manifest, reports)
        validation = self._validator.validate(request, files, reports)
        handoff = self._handoff_service.build(request.version, validation, reports)
        manifest = self._build_manifest(
            request=request,
            package_name=package_name,
            files=files,
            reports=reports,
            created_at=created_at,
        )
        checksums = {file.file_path: file.sha256 for file in files if file.included}
        package_path = self._package_path(request.output_dir, package_name)
        status = "dry_run" if request.dry_run else "created"
        package = ReleasePackage(
            release_package_id=release_package_id,
            version=request.version,
            status=cast(Any, status),
            package_name=package_name,
            package_path=package_path.as_posix(),
            manifest=manifest,
            files=files,
            checksums=checksums,
            validation=validation,
            handoff_report=handoff,
            created_by=request.created_by,
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )
        if not request.dry_run:
            self._write_package(package, reports, package_path)
        saved = self._repository.save(package)
        record_audit_event(
            self._audit_sink,
            action_type="release.package.create",
            resource_type="release_package",
            resource_id=saved.release_package_id,
            event_type="release_package_created",
            outcome="dry_run" if saved.status == "dry_run" else "completed",
            source_component="release_packager",
            actor_id=request.created_by,
            payload={
                "version": saved.version,
                "status": saved.status,
                "validation": saved.validation.status,
            },
        )
        self._emit(
            "release_package_created",
            saved.release_package_id,
            request.owner_scope,
            0.9 if saved.validation.status != "failed" else 1.0,
            {
                "version": saved.version,
                "status": saved.status,
                "validation": saved.validation.status,
            },
        )
        return saved

    def get(self, release_package_id: str, scope: builtins.list[str]) -> ReleasePackage | None:
        """Return one release package."""
        self._authorize_read(scope, release_package_id)
        return self._repository.get(release_package_id)

    def list(
        self,
        scope: builtins.list[str],
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> builtins.list[ReleasePackage]:
        """List release packages."""
        self._authorize_read(scope, None)
        return self._repository.list(version=version, status=status)

    def validate_package(
        self,
        release_package_id: str,
        scope: builtins.list[str],
    ) -> ReleasePackageValidation:
        """Return stored validation after a validation policy gate."""
        self._authorize(
            "release.package.validate",
            scope,
            resource_id=release_package_id,
            risk_level="low",
        )
        package = self._repository.get(release_package_id)
        if package is None:
            raise AIONNotFoundException("release_package_not_found")
        return package.validation

    def handoff(
        self,
        release_package_id: str,
        scope: builtins.list[str],
    ) -> ReleaseHandoffReport:
        """Return the stored handoff report."""
        self._authorize(
            "release.handoff.read",
            scope,
            resource_id=release_package_id,
            risk_level="low",
        )
        package = self._repository.get(release_package_id)
        if package is None:
            raise AIONNotFoundException("release_package_not_found")
        return package.handoff_report

    def _collect_reports(
        self,
        request: ReleasePackageRequest,
        app: object | None,
    ) -> dict[str, Any]:
        reports: dict[str, Any] = {}
        reports["source_manifest"] = self._source_manifest_service.build(self._root_dir)
        _set_if_present(
            reports,
            "version_manifest",
            _try_call(
                self._version_manifest_service,
                "create_manifest",
                request.version,
                request.created_by,
                request.owner_scope,
                app=app,
            ),
        )
        if request.include_contracts:
            _set_if_present(
                reports,
                "contract_export",
                _try_call(self._contract_export_service, "export_contracts", app)
                if app is not None
                else {"status": "warning", "message": "app_context_unavailable"},
            )
            reports["contract_registry"] = self._contract_registry_summary(request.owner_scope)
            reports["extension_registry"] = self._extension_registry_summary(request.owner_scope)
            reports["module_binding_registry"] = self._module_binding_summary(request.owner_scope)
            reports["capability_conformance"] = self._conformance_summary(request.owner_scope)
        if request.include_policy_bundle:
            reports["policy_bundle"] = self._policy_bundle_report()
        if request.include_migration_baseline:
            _set_if_present(
                reports,
                "migration_baseline",
                _try_call(
                    self._migration_baseline_service,
                    "generate",
                    request.version,
                    request.owner_scope,
                ),
            )
        _set_if_present(
            reports,
            "compatibility_matrix",
            _try_call(
                self._compatibility_matrix_service,
                "generate",
                request.version,
                request.owner_scope,
            ),
        )
        _set_if_present(
            reports,
            "release_artifact_manifest",
            _try_call(
                self._release_artifact_service,
                "generate",
                request.version,
                request.created_by,
                request.owner_scope,
            ),
        )
        if request.include_release_baseline:
            reports["release_baseline"] = self._release_baseline_report(request)
        if request.include_freeze_gate:
            reports["freeze_gate"] = self._freeze_gate_report(request, app)
        reports["hardening_gate"] = self._hardening_gate_report(request)
        if (
            request.include_sbom_placeholder
            and self._settings.release_package_sbom_placeholder_enabled
        ):
            reports["sbom"] = self._sbom_service.generate(request.version)
        reports["no_domain_drift"] = {"status": "passed", "message": "generic Brain core only"}
        reports["autonomy_defaults"] = {
            "full_autonomy_enabled": False,
            "max_mode": self._settings.autonomy_default_max_mode,
        }
        return reports

    def _policy_bundle_report(self) -> dict[str, Any]:
        export = getattr(self._policy_bundle_service, "export_bundle", None)
        if callable(export):
            try:
                payload = _jsonable(export())
                if isinstance(payload, dict):
                    return payload
                return {"status": "warning", "message": "policy_bundle_export_not_object"}
            except TypeError:
                return {"status": "warning", "message": "policy_bundle_requires_request"}
            except Exception as exc:
                return {"status": "warning", "message": exc.__class__.__name__}
        return {"status": "warning", "message": "policy_bundle_service_unavailable"}

    def _contract_registry_summary(self, scope: builtins.list[str]) -> dict[str, Any]:
        latest_snapshot = _try_call(self._contract_registry_repository, "latest_snapshot")
        latest_scan = _try_call(self._contract_registry_repository, "latest_scan")
        report = _try_call(self._contract_registry_report_service, "generate", scope)
        available = latest_snapshot is not None or latest_scan is not None or report is not None
        return {
            "available": available,
            "status": "available" if available else "warning",
            "snapshot": _snapshot_summary(latest_snapshot),
            "compatibility_scan": _scan_summary(latest_scan),
            "report": _report_summary(report),
            "full_schemas_included": False,
            "source_code_is_source_of_truth": True,
        }

    def _extension_registry_summary(self, scope: builtins.list[str]) -> dict[str, Any]:
        status = _try_call(self._extension_registry_repository, "status", scope)
        packages = _try_call(self._extension_registry_repository, "list_packages", limit=500)
        if not isinstance(packages, list):
            packages = []
        blocked = [
            item
            for item in packages
            if getattr(item, "compatibility_status", None) in {"blocked", "failed"}
        ]
        return {
            "available": self._extension_registry_repository is not None,
            "status": (
                "blocked"
                if blocked
                else _jsonable(status).get("status", "warning")
                if isinstance(_jsonable(status), dict)
                else "warning"
            ),
            "package_count": len(packages),
            "blocked_count": len(blocked),
            "metadata_only": True,
            "code_loading_allowed": False,
            "activation_allowed": False,
            "source_code_is_source_of_truth": True,
        }

    def _module_binding_summary(self, scope: builtins.list[str]) -> dict[str, Any]:
        status = _try_call(self._module_binding_repository, "status", scope)
        slots = _try_call(self._module_binding_repository, "list_slots", limit=500)
        bindings = _try_call(self._module_binding_repository, "list_bindings", limit=500)
        plans = _try_call(self._module_binding_repository, "list_mount_plans", limit=500)
        conflicts = _try_call(self._module_binding_repository, "list_conflicts", limit=500)
        slots = slots if isinstance(slots, list) else []
        bindings = bindings if isinstance(bindings, list) else []
        plans = plans if isinstance(plans, list) else []
        conflicts = conflicts if isinstance(conflicts, list) else []
        open_conflicts = [item for item in conflicts if getattr(item, "status", None) == "open"]
        return {
            "available": self._module_binding_repository is not None,
            "status": (
                "blocked"
                if open_conflicts
                else _jsonable(status).get("status", "warning")
                if isinstance(_jsonable(status), dict)
                else "warning"
            ),
            "module_slot_count": len(slots),
            "capability_binding_count": len(bindings),
            "module_mount_plan_count": len(plans),
            "open_conflict_count": len(open_conflicts),
            "metadata_only": True,
            "activation_allowed": False,
            "execution_allowed": False,
            "dynamic_route_registration_allowed": False,
            "source_code_is_source_of_truth": True,
        }

    def _conformance_summary(self, scope: builtins.list[str]) -> dict[str, Any]:
        status = _try_call(self._conformance_repository, "status", scope)
        runs = _try_call(self._conformance_repository, "list_runs", limit=500)
        findings = _try_call(
            self._conformance_repository,
            "list_findings",
            status="open",
            limit=500,
        )
        readiness = _try_call(self._conformance_repository, "list_readiness", limit=500)
        runs = runs if isinstance(runs, list) else []
        findings = findings if isinstance(findings, list) else []
        readiness = readiness if isinstance(readiness, list) else []
        failed_runs = [
            item for item in runs if getattr(item, "status", None) in {"failed", "blocked"}
        ]
        blocked_readiness = [
            item for item in readiness if getattr(item, "status", None) == "blocked"
        ]
        return {
            "available": self._conformance_repository is not None,
            "status": (
                "blocked"
                if failed_runs or blocked_readiness
                else _jsonable(status).get("status", "warning")
                if isinstance(_jsonable(status), dict)
                else "warning"
            ),
            "conformance_run_count": len(runs),
            "failed_conformance_count": len(failed_runs),
            "open_finding_count": len(findings),
            "readiness_assessment_count": len(readiness),
            "blocked_readiness_count": len(blocked_readiness),
            "metadata_only": True,
            "activation_allowed": False,
            "code_loading_allowed": False,
            "external_calls_allowed": False,
            "source_code_is_source_of_truth": True,
        }

    def _release_baseline_report(self, request: ReleasePackageRequest) -> Any:
        from aion_brain.contracts.release_baseline import ReleaseBaselineRequest

        return _try_call(
            self._release_baseline_service,
            "run",
            ReleaseBaselineRequest(
                version=request.version,
                owner_scope=request.owner_scope,
                include_quality_gates=False,
                created_by=request.created_by,
            ),
        ) or {"status": "warning", "message": "release_baseline_unavailable"}

    def _freeze_gate_report(
        self,
        request: ReleasePackageRequest,
        app: object | None,
    ) -> Any:
        from aion_brain.contracts.freeze import FreezeGateRunRequest

        run = getattr(self._freeze_gate_service, "run", None)
        if not callable(run):
            return {"status": "warning", "message": "freeze_gate_service_unavailable"}
        try:
            return run(
                FreezeGateRunRequest(
                    version=request.version,
                    owner_scope=request.owner_scope,
                    requested_by=request.created_by,
                    include_contract_export=False,
                    include_release_baseline=False,
                    include_kernel_self_test=False,
                    include_policy_coverage=False,
                    include_openapi_hygiene=False,
                    include_boundary_check=False,
                    include_no_domain_drift=False,
                    include_repo_health=False,
                    dry_run=True,
                ),
                app=app,
            )
        except Exception as exc:
            return {"status": "warning", "message": exc.__class__.__name__}

    def _hardening_gate_report(self, request: ReleasePackageRequest) -> Any:
        from aion_brain.contracts.security_baseline import HardeningGateRequest

        run = getattr(self._hardening_gate_service, "run", None)
        if not callable(run):
            return {"status": "warning", "message": "hardening_gate_service_unavailable"}
        try:
            return run(
                HardeningGateRequest(
                    version=request.version,
                    owner_scope=request.owner_scope,
                    include_secret_scan=False,
                    include_api_exposure_check=False,
                    include_policy_coverage_check=False,
                    created_by=request.created_by,
                )
            )
        except Exception as exc:
            return {"status": "warning", "message": exc.__class__.__name__}

    def _build_files(
        self,
        release_package_id: str,
        source_manifest: object,
        reports: dict[str, Any],
    ) -> builtins.list[ReleasePackageFile]:
        created_at = datetime.now(UTC)
        files: builtins.list[ReleasePackageFile] = []
        if isinstance(source_manifest, dict):
            for item in source_manifest.get("files", []):
                if isinstance(item, dict):
                    files.append(
                        ReleasePackageFile(
                            release_package_file_id=f"release-file-{uuid4().hex}",
                            release_package_id=release_package_id,
                            file_path=str(item["file_path"]),
                            artifact_type=cast(Any, item.get("artifact_type", "source")),
                            size_bytes=int(item.get("size_bytes", 0)),
                            sha256=str(item.get("sha256", "")),
                            included=bool(item.get("included", True)),
                            reason=cast(str | None, item.get("reason")),
                            created_at=created_at,
                        )
                    )
        for name, payload in _generated_artifacts(reports).items():
            encoded = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode()
            files.append(
                ReleasePackageFile(
                    release_package_file_id=f"release-file-{uuid4().hex}",
                    release_package_id=release_package_id,
                    file_path=f"generated/{name}.json",
                    artifact_type=_artifact_type_for_generated(name),
                    size_bytes=len(encoded),
                    sha256=sha256_bytes(encoded),
                    included=True,
                    reason=None,
                    created_at=created_at,
                )
            )
        return sorted(files, key=lambda item: item.file_path)

    def _build_manifest(
        self,
        *,
        request: ReleasePackageRequest,
        package_name: str,
        files: builtins.list[ReleasePackageFile],
        reports: dict[str, Any],
        created_at: datetime,
    ) -> ReleasePackageManifest:
        included = [file for file in files if file.included]
        checksums = {file.file_path: file.sha256 for file in included}
        source_manifest = reports.get("source_manifest")
        excluded = []
        if isinstance(source_manifest, dict):
            excluded = list(source_manifest.get("excluded_artifacts", []))
        return ReleasePackageManifest(
            version=request.version,
            package_name=package_name,
            created_at=created_at,
            included_artifacts=sorted({file.artifact_type for file in included}),
            excluded_artifacts=excluded,
            file_count=len(included),
            total_size_bytes=sum(file.size_bytes for file in included),
            root_checksum=root_checksum(checksums),
            metadata={
                "dry_run": request.dry_run,
                "local_only": True,
                "external_calls": False,
                "reports": sorted(reports),
                **request.metadata,
            },
        )

    def _package_path(self, output_dir: str, package_name: str) -> Path:
        output_root = (self._root_dir / output_dir).resolve()
        if not _is_relative_to(output_root, self._root_dir.resolve()):
            raise AIONUnsupportedOperationException("release_package_output_outside_repo")
        return output_root / package_name

    def _write_package(
        self,
        package: ReleasePackage,
        reports: dict[str, Any],
        package_dir: Path,
    ) -> None:
        package_dir.mkdir(parents=True, exist_ok=True)
        generated = {
            "release-package-manifest": package.manifest.model_dump(mode="json"),
            "checksums": package.checksums,
            "handoff-report": package.handoff_report.model_dump(mode="json"),
            "validation-report": package.validation.model_dump(mode="json"),
            **_generated_artifacts(reports),
        }
        for name, payload in generated.items():
            path = package_dir / f"{name}.json"
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        archive_path = package_dir.with_suffix(".tar.gz")
        with tarfile.open(archive_path, "w:gz") as archive:
            for child in sorted(package_dir.rglob("*")):
                if child.is_file():
                    archive.add(child, arcname=child.relative_to(package_dir.parent))

    def _authorize(
        self,
        action_type: str,
        scope: builtins.list[str],
        *,
        actor_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="release_package",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _authorize_read(self, scope: builtins.list[str], resource_id: str | None) -> None:
        self._authorize(
            "release.package.read",
            scope,
            resource_id=resource_id,
            risk_level="low",
        )

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: builtins.list[str],
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="release_package",
            node_id=node_id,
            intensity=intensity,
            scope=scope,
            payload=payload,
        )


def _try_call(service: object | None, method_name: str, *args: Any, **kwargs: Any) -> Any:
    method = getattr(service, method_name, None)
    if not callable(method):
        return None
    try:
        return method(*args, **kwargs)
    except Exception as exc:
        return {"status": "warning", "message": exc.__class__.__name__}


def _set_if_present(reports: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        reports[key] = value


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def _generated_artifacts(reports: dict[str, Any]) -> dict[str, Any]:
    generated: dict[str, Any] = {}
    for name, payload in reports.items():
        safe_name = name.replace("_", "-")
        generated[safe_name] = _jsonable(payload)
    return generated


def _artifact_type_for_generated(name: str) -> Any:
    normalized = name.replace("-", "_")
    if normalized == "sbom":
        return "sbom"
    if normalized == "contract_export":
        return "contract"
    if normalized == "policy_bundle":
        return "policy"
    if normalized == "migration_baseline":
        return "migration"
    if normalized == "source_manifest":
        return "manifest"
    return "report"


def _snapshot_summary(value: Any) -> dict[str, Any]:
    if not hasattr(value, "contract_snapshot_id"):
        return {"available": False}
    return {
        "available": True,
        "contract_snapshot_id": getattr(value, "contract_snapshot_id", None),
        "status": getattr(value, "status", None),
        "root_hash": getattr(value, "root_hash", None),
        "contract_count": getattr(value, "contract_count", 0),
        "interface_count": getattr(value, "interface_count", 0),
        "created_at": str(getattr(value, "created_at", None)),
    }


def _scan_summary(value: Any) -> dict[str, Any]:
    if not hasattr(value, "compatibility_scan_id"):
        return {"available": False}
    return {
        "available": True,
        "compatibility_scan_id": getattr(value, "compatibility_scan_id", None),
        "status": getattr(value, "status", None),
        "findings_count": getattr(value, "findings_count", 0),
        "breaking_count": getattr(value, "breaking_count", 0),
        "warning_count": getattr(value, "warning_count", 0),
    }


def _report_summary(value: Any) -> dict[str, Any]:
    if not hasattr(value, "contract_report_id"):
        return {"available": False}
    return {
        "available": True,
        "contract_report_id": getattr(value, "contract_report_id", None),
        "status": getattr(value, "status", None),
        "active_breaking_findings": getattr(value, "active_breaking_findings", 0),
        "active_warning_findings": getattr(value, "active_warning_findings", 0),
        "missing_sdk_count": getattr(value, "missing_sdk_count", 0),
        "missing_cli_count": getattr(value, "missing_cli_count", 0),
        "missing_policy_count": getattr(value, "missing_policy_count", 0),
    }


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
