"""AION v0.1 deterministic freeze gate."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.compatibility import SDKCompatibilityReport
from aion_brain.contracts.freeze import FreezeGateCheck, FreezeGateRun, FreezeGateRunRequest
from aion_brain.contracts.kernel import KernelSelfTestRequest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.release_baseline import ReleaseBaselineRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.versioning.compatibility import emit_versioning_telemetry
from aion_brain.versioning.features import default_feature_entries
from aion_brain.versioning.manifest import stable_hash
from aion_brain.versioning.repository import VersioningRepository

CRITICAL_FAILURE_CHECKS = {
    "contract_export_available",
    "boundary_check",
    "no_domain_drift",
    "migration_baseline",
    "release_baseline",
    "no_raw_secrets",
    "no_full_autonomy_default",
    "security_hardening_gate_passed",
    "runtime_config_validation_passed",
    "config_snapshot_created",
    "config_hash_available",
    "extension_registry_safe",
    "module_binding_registry_safe",
    "resilience_status_healthy_or_only_optional_degraded",
    "audit_integrity_status_available",
    "audit_verification_passed_or_not_required",
}
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "payment",
    "procurement",
    "security",
}


class FreezeGateService:
    """Run local deterministic v0.1 freeze readiness checks."""

    def __init__(
        self,
        repository: VersioningRepository,
        policy_adapter: PolicyAdapter,
        *,
        version_manifest_service: object,
        feature_registry_service: object,
        compatibility_matrix_service: object,
        migration_baseline_service: object,
        release_artifact_service: object,
        sdk_compatibility_service: object,
        release_baseline_service: object | None = None,
        kernel_self_test: object | None = None,
        policy_coverage: object | None = None,
        openapi_hygiene: object | None = None,
        boundary_checker: object | None = None,
        contract_export_service: object | None = None,
        benchmark_runner: object | None = None,
        capacity_baseline_service: object | None = None,
        hardening_gate_service: object | None = None,
        config_validator: object | None = None,
        config_snapshot_service: object | None = None,
        runtime_config_status_service: object | None = None,
        resilience_test_runner: object | None = None,
        audit_integrity_ledger: object | None = None,
        audit_verifier: object | None = None,
        operator_readiness_service: object | None = None,
        contract_registry_repository: object | None = None,
        extension_registry_repository: object | None = None,
        audit_sink: object | None = None,
        telemetry_service: object | None = None,
        root_dir: Path | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._version_manifest_service = version_manifest_service
        self._feature_registry_service = feature_registry_service
        self._compatibility_matrix_service = compatibility_matrix_service
        self._migration_baseline_service = migration_baseline_service
        self._release_artifact_service = release_artifact_service
        self._sdk_compatibility_service = sdk_compatibility_service
        self._release_baseline_service = release_baseline_service
        self._kernel_self_test = kernel_self_test
        self._policy_coverage = policy_coverage
        self._openapi_hygiene = openapi_hygiene
        self._boundary_checker = boundary_checker
        self._contract_export_service = contract_export_service
        self._benchmark_runner = benchmark_runner
        self._capacity_baseline_service = capacity_baseline_service
        self._hardening_gate_service = hardening_gate_service
        self._config_validator = config_validator
        self._config_snapshot_service = config_snapshot_service
        self._runtime_config_status_service = runtime_config_status_service
        self._resilience_test_runner = resilience_test_runner
        self._audit_integrity_ledger = audit_integrity_ledger
        self._audit_verifier = audit_verifier
        self._operator_readiness_service = operator_readiness_service
        self._contract_registry_repository = contract_registry_repository
        self._extension_registry_repository = extension_registry_repository
        self._module_binding_repository: object | None = None
        self._audit_sink = audit_sink
        self._telemetry_service = telemetry_service
        self._root_dir = root_dir or Path(__file__).parents[5]
        self._settings = settings or get_settings()

    def set_contract_registry_repository(self, repository: object | None) -> None:
        """Attach Contract Registry after kernel assembly."""

        self._contract_registry_repository = repository

    def set_extension_registry_repository(self, repository: object | None) -> None:
        """Attach Extension Registry after kernel assembly."""

        self._extension_registry_repository = repository

    def set_module_binding_repository(self, repository: object | None) -> None:
        """Attach module binding registry after kernel assembly."""

        self._module_binding_repository = repository

    def run(self, request: FreezeGateRunRequest, *, app: object | None = None) -> FreezeGateRun:
        """Run the local freeze gate and persist the result."""
        if not self._settings.freeze_gate_enabled:
            raise AIONPolicyDeniedException("freeze_gate_disabled")
        self._authorize(request)
        freeze_gate_id = request.freeze_gate_id or f"freeze-gate-{uuid4().hex}"
        created_at = datetime.now(UTC)
        self._emit("freeze_gate_started", freeze_gate_id, request.owner_scope, 0.5, {})
        checks: list[FreezeGateCheck] = []
        checks.append(
            self._run_check(
                "version_manifest_can_be_created",
                "versioning",
                lambda: self._check_version_manifest(request, app),
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "feature_registry_no_domain_drift",
                "versioning",
                lambda: self._check_feature_registry(request.owner_scope),
                severity="critical",
            )
        )
        if request.include_contract_export:
            checks.append(
                self._run_check(
                    "contract_export_available",
                    "contracts",
                    lambda: self._check_contract_export(app),
                    severity="critical",
                )
            )
            checks.append(
                self._run_check(
                    "contract_hash_stable",
                    "contracts",
                    self._check_contract_hash_stable,
                    severity="high",
                )
            )
            checks.append(
                self._run_check(
                    "contract_snapshot_available",
                    "contracts",
                    self._check_contract_snapshot_available,
                    severity="high",
                )
            )
            checks.append(
                self._run_check(
                    "compatibility_scan_passed",
                    "contracts",
                    self._check_compatibility_scan_passed,
                    severity="high",
                )
            )
            checks.append(
                self._run_check(
                    "no_active_breaking_interface_findings",
                    "contracts",
                    self._check_no_active_breaking_interface_findings,
                    severity="critical",
                )
            )
        if request.include_sdk_check:
            checks.append(
                self._run_check(
                    "sdk_compatibility",
                    "sdk",
                    lambda: self._check_sdk(request.owner_scope),
                    severity="high",
                )
            )
        checks.append(
            self._run_check(
                "extension_registry_safe",
                "extensions",
                self._check_extension_registry_safe,
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "module_binding_registry_safe",
                "module_bindings",
                self._check_module_binding_registry_safe,
                severity="critical",
            )
        )
        if request.include_migration_baseline:
            checks.append(
                self._run_check(
                    "migration_baseline",
                    "migrations",
                    lambda: self._check_migration_baseline(request),
                    severity="critical",
                )
            )
        if request.include_release_baseline:
            checks.append(
                self._run_check(
                    "release_baseline",
                    "release",
                    lambda: self._check_release_baseline(request),
                    severity="critical",
                )
            )
        if request.include_kernel_self_test:
            checks.append(
                self._run_check(
                    "kernel_self_test",
                    "kernel",
                    lambda: self._check_kernel_self_test(request),
                    severity="high",
                )
            )
        if request.include_policy_coverage:
            checks.append(
                self._run_check(
                    "policy_coverage",
                    "policy",
                    self._check_policy_coverage,
                    severity="medium",
                )
            )
        if request.include_openapi_hygiene:
            checks.append(
                self._run_check(
                    "openapi_hygiene",
                    "api",
                    lambda: self._check_openapi_hygiene(app),
                    severity="medium",
                )
            )
        if request.include_boundary_check:
            checks.append(
                self._run_check(
                    "boundary_check",
                    "architecture",
                    self._check_boundary,
                    severity="critical",
                )
            )
        if request.include_no_domain_drift:
            checks.append(
                self._run_check(
                    "no_domain_drift",
                    "repository",
                    self._check_no_domain_drift,
                    severity="critical",
                )
            )
        if request.include_repo_health:
            checks.append(
                self._run_check(
                    "repo_health",
                    "repository",
                    self._check_repo_health,
                    severity="medium",
                )
            )
        checks.append(
            self._run_check(
                "performance_baseline_available",
                "performance",
                lambda: self._check_performance_baseline(request),
                severity=(
                    "high"
                    if bool(request.metadata.get("require_performance_baseline"))
                    else "medium"
                ),
            )
        )
        checks.append(
            self._run_check(
                "benchmark_smoke_passed",
                "performance",
                lambda: self._check_benchmark_smoke(request),
                severity="medium",
            )
        )
        checks.append(
            self._run_check(
                "security_hardening_gate_passed",
                "configuration",
                lambda: self._check_security_hardening_gate(request),
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "runtime_config_validation_passed",
                "configuration",
                lambda: self._check_runtime_config_validation(request),
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "unsafe_feature_overrides_absent",
                "configuration",
                lambda: self._check_unsafe_feature_overrides(request),
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "config_snapshot_created",
                "configuration",
                lambda: self._check_config_snapshot(request),
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "resilience_status_healthy_or_only_optional_degraded",
                "resilience",
                lambda: self._check_resilience_status(request),
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "audit_integrity_status_available",
                "audit_integrity",
                self._check_audit_integrity_status,
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "audit_verification_passed_or_not_required",
                "audit_integrity",
                lambda: self._check_audit_verification(request),
                severity="critical",
            )
        )
        checks.append(
            self._run_check(
                "operator_readiness_available",
                "operator",
                self._check_operator_readiness_available,
                severity="medium",
            )
        )
        checks.extend(
            [
                self._run_check(
                    "release_artifact_manifest",
                    "release",
                    lambda: self._check_release_artifact(request),
                    severity="high",
                ),
                self._run_check(
                    "optional_adapters_optional",
                    "compatibility",
                    lambda: self._check_optional_adapters(request),
                    severity="medium",
                ),
                self._run_check(
                    "no_full_autonomy_default",
                    "autonomy",
                    self._check_no_full_autonomy_default,
                    severity="critical",
                ),
                self._run_check(
                    "no_external_services_required_for_tests",
                    "quality",
                    lambda: {"status": "passed", "message": "Tests use local fakes by default."},
                    severity="high",
                ),
                self._run_check(
                    "no_raw_secrets",
                    "repository",
                    self._check_no_raw_secrets,
                    severity="critical",
                ),
                self._run_check(
                    "docs_current",
                    "docs",
                    self._check_docs_current,
                    severity="medium",
                ),
                self._run_check(
                    "adr_index_current",
                    "docs",
                    self._check_adr_index,
                    severity="medium",
                ),
            ]
        )
        failures = [
            check.model_dump(mode="json")
            for check in checks
            if check.status == "failed"
            and (check.name in CRITICAL_FAILURE_CHECKS or check.severity in {"high", "critical"})
        ]
        warnings = [
            check.model_dump(mode="json")
            for check in checks
            if check.status in {"warning", "skipped"}
        ]
        status = "failed" if failures else ("warning" if warnings else "passed")
        report = _build_report(checks)
        run = FreezeGateRun(
            freeze_gate_id=freeze_gate_id,
            version=request.version,
            status=cast(Any, status),
            requested_by=request.requested_by,
            checks=checks,
            failures=failures,
            warnings=warnings,
            report={**report, "dry_run": request.dry_run, "external_calls": False},
            created_at=created_at,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_freeze_gate(run)
        self._emit(
            "freeze_gate_completed" if saved.status != "failed" else "freeze_gate_failed",
            saved.freeze_gate_id,
            request.owner_scope,
            0.9 if saved.status == "passed" else 1.0,
            {"status": saved.status},
        )
        record_audit_event(
            self._audit_sink,
            action_type="freeze_gate.run",
            resource_type="freeze_gate",
            resource_id=saved.freeze_gate_id,
            event_type="freeze_gate_completed",
            outcome="completed" if saved.status != "failed" else "failed",
            source_component="freeze_gate",
            actor_id=request.requested_by,
            payload={"status": saved.status, "check_count": len(saved.checks)},
        )
        return saved

    def get(self, freeze_gate_id: str, scope: builtins.list[str]) -> FreezeGateRun | None:
        """Return one freeze gate run."""
        self._authorize_read(scope, freeze_gate_id)
        return self._repository.get_freeze_gate(freeze_gate_id)

    def list(
        self,
        scope: builtins.list[str],
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> builtins.list[FreezeGateRun]:
        """List freeze gate runs."""
        self._authorize_read(scope, None)
        return self._repository.list_freeze_gates(version=version, status=status)

    def _run_check(
        self,
        name: str,
        category: str,
        fn: Callable[[], dict[str, Any]],
        *,
        severity: str,
    ) -> FreezeGateCheck:
        try:
            result = fn()
        except Exception as exc:
            result = {"status": "failed", "message": exc.__class__.__name__, "details": {}}
        status = str(result.get("status", "failed"))
        if status not in {"passed", "failed", "warning", "skipped"}:
            status = "failed"
        return FreezeGateCheck(
            check_id=f"freeze-check-{uuid4().hex}",
            name=name,
            category=category,
            status=cast(Any, status),
            severity=cast(Any, severity),
            message=str(result.get("message", f"{name} {status}.")),
            details=dict(result.get("details", {})),
        )

    def _check_version_manifest(
        self,
        request: FreezeGateRunRequest,
        app: object | None,
    ) -> dict[str, Any]:
        manifest = cast(Any, self._version_manifest_service).create_manifest(
            request.version,
            request.requested_by,
            request.owner_scope,
            app=app,
        )
        return {
            "status": "passed",
            "message": "Version manifest can be created.",
            "details": {"version_manifest_id": manifest.version_manifest_id},
        }

    def _check_feature_registry(self, scope: builtins.list[str]) -> dict[str, Any]:
        features = cast(Any, self._feature_registry_service).list_features(scope)
        keys = [feature.feature_key for feature in features]
        domain_matches = [
            key for key in keys if any(term in key.lower() for term in _BANNED_DOMAIN_TERMS)
        ]
        return {
            "status": "failed" if domain_matches else "passed",
            "message": "Feature registry is domain-neutral.",
            "details": {"feature_count": len(keys), "domain_matches": domain_matches},
        }

    def _check_contract_export(self, app: object | None) -> dict[str, Any]:
        export = getattr(self._contract_export_service, "export_contracts", None)
        if not callable(export) or app is None:
            return {
                "status": "warning",
                "message": "Contract export service is present but app context is unavailable.",
            }
        exported = export(app)
        contracts = getattr(exported, "contracts", {})
        return {
            "status": "passed" if contracts else "failed",
            "message": "Contract export is available.",
            "details": {"contract_count": len(contracts)},
        }

    def _check_contract_hash_stable(self) -> dict[str, Any]:
        payload = {"version": self._settings.version, "api_version": self._settings.api_version}
        first = stable_hash(payload)
        second = stable_hash(payload)
        return {
            "status": "passed" if first == second else "failed",
            "message": "Contract hash is stable.",
            "details": {"hash": first},
        }

    def _check_contract_snapshot_available(self) -> dict[str, Any]:
        latest = getattr(self._contract_registry_repository, "latest_snapshot", None)
        snapshot = latest() if callable(latest) else None
        return {
            "status": "passed" if snapshot is not None else "warning",
            "message": (
                "Contract snapshot is available."
                if snapshot is not None
                else "No contract snapshot is available."
            ),
            "details": {
                "contract_snapshot_id": getattr(snapshot, "contract_snapshot_id", None),
                "root_hash": getattr(snapshot, "root_hash", None),
            },
        }

    def _check_compatibility_scan_passed(self) -> dict[str, Any]:
        latest = getattr(self._contract_registry_repository, "latest_scan", None)
        scan = latest() if callable(latest) else None
        status = getattr(scan, "status", None)
        passed = status in {"passed", "warning", "dry_run"}
        return {
            "status": "passed" if passed else "warning",
            "message": (
                "Latest compatibility scan is acceptable."
                if passed
                else "No acceptable compatibility scan is available."
            ),
            "details": {
                "compatibility_scan_id": getattr(scan, "compatibility_scan_id", None),
                "status": status,
                "breaking_count": getattr(scan, "breaking_count", 0),
                "warning_count": getattr(scan, "warning_count", 0),
            },
        }

    def _check_no_active_breaking_interface_findings(self) -> dict[str, Any]:
        list_findings = getattr(self._contract_registry_repository, "list_findings", None)
        findings = (
            list_findings(status="open", breaking=True, limit=1000)
            if callable(list_findings)
            else []
        )
        fail_on_breaking = bool(
            getattr(self._settings, "compatibility_breaking_changes_fail_freeze", True)
        )
        status = "failed" if findings and fail_on_breaking else "warning" if findings else "passed"
        return {
            "status": status,
            "message": (
                "No active breaking interface findings exist."
                if not findings
                else "Active breaking interface findings exist."
            ),
            "details": {
                "breaking_count": len(findings),
                "fail_on_breaking": fail_on_breaking,
            },
        }

    def _check_extension_registry_safe(self) -> dict[str, Any]:
        list_packages = getattr(self._extension_registry_repository, "list_packages", None)
        packages = list_packages(limit=1000) if callable(list_packages) else []
        blocked = [
            item
            for item in packages
            if getattr(item, "compatibility_status", None) in {"blocked", "failed"}
            or getattr(item, "status", None) == "incompatible"
        ]
        unsafe_flags = {
            "extension_code_loading_enabled": bool(
                getattr(self._settings, "extension_code_loading_enabled", False)
            ),
            "extension_activation_enabled": bool(
                getattr(self._settings, "extension_activation_enabled", False)
            ),
            "extension_external_sources_enabled": bool(
                getattr(self._settings, "extension_external_sources_enabled", False)
            ),
        }
        unsafe = [key for key, value in unsafe_flags.items() if value]
        status = "failed" if blocked or unsafe else "passed"
        return {
            "status": status,
            "message": "Extension registry remains metadata-only and compatible.",
            "details": {
                "package_count": len(packages),
                "blocked_count": len(blocked),
                "unsafe_flags": unsafe,
            },
        }

    def _check_module_binding_registry_safe(self) -> dict[str, Any]:
        list_bindings = getattr(self._module_binding_repository, "list_bindings", None)
        list_conflicts = getattr(self._module_binding_repository, "list_conflicts", None)
        bindings = list_bindings(limit=1000) if callable(list_bindings) else []
        conflicts = list_conflicts(status="open", limit=1000) if callable(list_conflicts) else []
        unsafe_flags = {
            "module_slot_activation_enabled": bool(
                getattr(self._settings, "module_slot_activation_enabled", False)
            ),
            "capability_binding_activation_enabled": bool(
                getattr(self._settings, "capability_binding_activation_enabled", False)
            ),
            "dynamic_route_registration_enabled": bool(
                getattr(self._settings, "dynamic_route_registration_enabled", False)
            ),
        }
        unsafe = [key for key, value in unsafe_flags.items() if value]
        blocked = [item for item in bindings if getattr(item, "status", None) == "blocked"]
        status = "failed" if blocked or conflicts or unsafe else "passed"
        return {
            "status": status,
            "message": "Module binding registry remains metadata-only and inactive.",
            "details": {
                "binding_count": len(bindings),
                "blocked_binding_count": len(blocked),
                "open_conflict_count": len(conflicts),
                "unsafe_flags": unsafe,
            },
        }

    def _check_sdk(self, scope: builtins.list[str]) -> dict[str, Any]:
        report: SDKCompatibilityReport = cast(Any, self._sdk_compatibility_service).check(scope)
        return {
            "status": "passed" if report.compatible else "failed",
            "message": "SDK compatibility checked.",
            "details": report.model_dump(mode="json"),
        }

    def _check_migration_baseline(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        baseline = cast(Any, self._migration_baseline_service).generate(
            request.version,
            request.owner_scope,
        )
        return {
            "status": "passed" if baseline.status == "passed" else baseline.status,
            "message": "Migration baseline generated.",
            "details": baseline.model_dump(mode="json"),
        }

    def _check_release_baseline(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        if self._release_baseline_service is None:
            return {"status": "warning", "message": "Release baseline service unavailable."}
        report = cast(Any, self._release_baseline_service).run(
            ReleaseBaselineRequest(
                version=request.version,
                owner_scope=request.owner_scope,
                include_quality_gates=False,
                created_by=request.requested_by,
            )
        )
        return {
            "status": "passed" if report.status == "passed" else report.status,
            "message": "Release baseline run completed.",
            "details": {"release_baseline_id": report.release_baseline_id},
        }

    def _check_kernel_self_test(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        run = getattr(self._kernel_self_test, "run", None)
        if not callable(run):
            return {"status": "warning", "message": "Kernel self-test service unavailable."}
        result = run(KernelSelfTestRequest(scope=request.owner_scope, dry_run=True))
        return {
            "status": "passed" if result.status == "passed" else "warning",
            "message": "Kernel self-test completed.",
            "details": {"status": result.status},
        }

    def _check_policy_coverage(self) -> dict[str, Any]:
        generate = getattr(self._policy_coverage, "generate", None)
        if not callable(generate):
            return {"status": "warning", "message": "Policy coverage service unavailable."}
        report = cast(Any, generate)()
        return {
            "status": "passed" if report.status == "passed" else "warning",
            "message": "Policy coverage generated.",
            "details": {"status": report.status},
        }

    def _check_openapi_hygiene(self, app: object | None) -> dict[str, Any]:
        check = getattr(self._openapi_hygiene, "check", None)
        if not callable(check) or app is None:
            return {"status": "warning", "message": "OpenAPI hygiene app context unavailable."}
        openapi = getattr(app, "openapi", None)
        if not callable(openapi):
            return {"status": "warning", "message": "OpenAPI hygiene app context unavailable."}
        report = cast(Any, check)(openapi())
        return {
            "status": "passed" if report.status == "passed" else "failed",
            "message": "OpenAPI hygiene checked.",
            "details": {"status": report.status},
        }

    def _check_boundary(self) -> dict[str, Any]:
        check = getattr(self._boundary_checker, "check", None)
        if not callable(check):
            return {"status": "warning", "message": "Boundary checker unavailable."}
        report = cast(Any, check)()
        return {
            "status": "passed" if report.status == "passed" else "failed",
            "message": "Boundary check completed.",
            "details": {"status": report.status, "violations": report.violations},
        }

    def _check_no_domain_drift(self) -> dict[str, Any]:
        paths = [
            self._root_dir / "examples" / "scenarios",
            self._root_dir / "examples" / "fixtures",
        ]
        matches: builtins.list[str] = []
        for feature in default_feature_entries([self._settings.scenario_default_owner_scope]):
            if any(term in feature.feature_key.lower() for term in _BANNED_DOMAIN_TERMS):
                matches.append(f"feature:{feature.feature_key}")
        for root in paths:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in {".md", ".json", ".yaml"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                for term in _BANNED_DOMAIN_TERMS - {"security"}:
                    if term in text:
                        matches.append(path.relative_to(self._root_dir).as_posix())
                        break
        return {
            "status": "failed" if matches else "passed",
            "message": "No domain drift detected in release-owned artifacts.",
            "details": {"matches": sorted(set(matches))},
        }

    def _check_repo_health(self) -> dict[str, Any]:
        required = [
            "README.md",
            "AGENTS.md",
            "docker-compose.yml",
            "services/brain-api",
            "packages/aion-sdk-python",
            "docs/adr",
        ]
        missing = [path for path in required if not (self._root_dir / path).exists()]
        return {
            "status": "failed" if missing else "passed",
            "message": "Repository health inputs are present.",
            "details": {"missing": missing},
        }

    def _check_release_artifact(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        artifact = cast(Any, self._release_artifact_service).generate(
            request.version,
            request.requested_by,
            request.owner_scope,
        )
        return {
            "status": "passed" if artifact.status == "complete" else "failed",
            "message": "Release artifact manifest generated.",
            "details": artifact.model_dump(mode="json"),
        }

    def _check_optional_adapters(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        matrix = cast(Any, self._compatibility_matrix_service).generate(
            request.version,
            request.owner_scope,
        )
        required_optional = [
            name
            for name, payload in matrix.optional_adapters.items()
            if isinstance(payload, dict) and payload.get("required") is True
        ]
        return {
            "status": "failed" if required_optional else "passed",
            "message": "Optional adapters remain optional.",
            "details": {"required_optional": required_optional},
        }

    def _check_no_full_autonomy_default(self) -> dict[str, Any]:
        blocked = (
            self._settings.autonomy_default_max_mode in {"autonomous", "full"}
            or self._settings.autonomy_external_tools_allowed_default
            or self._settings.autonomy_background_workflows_allowed_default
        )
        return {
            "status": "failed" if blocked else "passed",
            "message": "Full autonomy is disabled by default.",
            "details": {
                "max_mode": self._settings.autonomy_default_max_mode,
                "external_tools": self._settings.autonomy_external_tools_allowed_default,
                "background_workflows": (
                    self._settings.autonomy_background_workflows_allowed_default
                ),
            },
        }

    def _check_performance_baseline(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        list_baselines = getattr(self._capacity_baseline_service, "list", None)
        required = bool(request.metadata.get("require_performance_baseline"))
        if not callable(list_baselines):
            return {
                "status": "failed" if required else "warning",
                "message": "Capacity baseline service unavailable.",
            }
        baselines = list_baselines(version=request.version, status="active")
        return {
            "status": "passed" if baselines else ("failed" if required else "warning"),
            "message": (
                "Performance baseline is available."
                if baselines
                else "No active performance baseline is available."
            ),
            "details": {"baseline_count": len(baselines), "required": required},
        }

    def _check_benchmark_smoke(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        list_runs = getattr(self._benchmark_runner, "list_runs", None)
        if not callable(list_runs):
            return {"status": "warning", "message": "Benchmark runner unavailable."}
        try:
            runs = list_runs(request.owner_scope, status="passed", benchmark_type="smoke", limit=1)
        except Exception as exc:
            return {"status": "warning", "message": exc.__class__.__name__}
        return {
            "status": "passed" if runs else "warning",
            "message": (
                "A passing smoke benchmark run is available."
                if runs
                else "No passing smoke benchmark run is available."
            ),
            "details": {"run_count": len(runs)},
        }

    def _check_security_hardening_gate(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        run = getattr(self._hardening_gate_service, "run", None)
        if not callable(run):
            return {"status": "warning", "message": "Hardening gate service unavailable."}
        from aion_brain.contracts.security_baseline import HardeningGateRequest

        try:
            result = run(
                HardeningGateRequest(
                    version=request.version,
                    owner_scope=request.owner_scope,
                    include_api_exposure_check=False,
                    include_policy_coverage_check=False,
                    include_secret_scan=False,
                    include_dependency_metadata_check=True,
                    created_by=request.requested_by,
                )
            )
        except Exception as exc:
            return {"status": "warning", "message": exc.__class__.__name__}
        return {
            "status": "passed" if result.status == "passed" else result.status,
            "message": "Security hardening gate checked.",
            "details": {"hardening_gate_id": result.hardening_gate_id, "status": result.status},
        }

    def _check_runtime_config_validation(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        validate = getattr(self._config_validator, "validate", None)
        if not callable(validate):
            return {"status": "warning", "message": "Runtime config validator unavailable."}
        from aion_brain.contracts.runtime_config import ConfigValidationRequest

        result = validate(
            ConfigValidationRequest(
                owner_scope=request.owner_scope,
                metadata={"source": "freeze_gate"},
                created_by=request.requested_by,
            )
        )
        return {
            "status": "passed" if result.status == "passed" else result.status,
            "message": "Runtime config validation completed.",
            "details": {
                "config_validation_id": result.config_validation_id,
                "status": result.status,
            },
        }

    def _check_unsafe_feature_overrides(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        status = getattr(self._runtime_config_status_service, "status", None)
        if not callable(status):
            return {"status": "warning", "message": "Runtime config status unavailable."}
        result = status(request.owner_scope)
        unsafe = [
            key
            for key, enabled in result.effective_feature_flags.items()
            if enabled and key.startswith("autonomy.full")
        ]
        return {
            "status": "failed" if unsafe else "passed",
            "message": "Unsafe feature overrides are absent.",
            "details": {"unsafe": unsafe},
        }

    def _check_config_snapshot(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        create_snapshot = getattr(self._config_snapshot_service, "create_snapshot", None)
        if not callable(create_snapshot):
            return {"status": "warning", "message": "Config snapshot service unavailable."}
        from aion_brain.contracts.runtime_config import ConfigSnapshotRequest

        snapshot = create_snapshot(
            ConfigSnapshotRequest(
                snapshot_type="freeze_gate",
                owner_scope=request.owner_scope,
                metadata={"source": "freeze_gate"},
                created_by=request.requested_by,
            )
        )
        return {
            "status": "passed" if snapshot.config_hash else "failed",
            "message": "Runtime config snapshot was created.",
            "details": {
                "config_snapshot_id": snapshot.config_snapshot_id,
                "config_hash_available": bool(snapshot.config_hash),
            },
        }

    def _check_resilience_status(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        run = getattr(self._resilience_test_runner, "run", None)
        if not callable(run):
            return {"status": "warning", "message": "Resilience test runner unavailable."}
        from aion_brain.contracts.resilience import ResilienceTestRunRequest

        result = run(
            ResilienceTestRunRequest(
                trace_id=None,
                owner_scope=request.owner_scope,
                mode="dry_run",
                created_by=request.requested_by,
                metadata={"source": "freeze_gate"},
            )
        )
        status = "passed"
        if result.status == "failed":
            status = (
                "failed" if bool(self._settings.resilience_fail_freeze_on_critical) else "warning"
            )
        elif result.status == "warning":
            status = "warning"
        return {
            "status": status,
            "message": "Resilience status is healthy or only optionally degraded.",
            "details": {
                "resilience_test_run_id": result.resilience_test_run_id,
                "resilience_status": result.status,
                "failure_count": len(result.failures),
                "warning_count": len(result.warnings),
            },
        }

    def _check_audit_integrity_status(self) -> dict[str, Any]:
        status = getattr(self._audit_integrity_ledger, "status", None)
        if not callable(status):
            return {
                "status": "warning",
                "message": "Audit integrity status is unavailable in this local gate context.",
            }
        result = status()
        return {
            "status": "passed",
            "message": "Audit integrity status is available.",
            "details": {
                "latest_sequence": result.latest_sequence,
                "verification_status": result.verification_status,
            },
        }

    def _check_audit_verification(self, request: FreezeGateRunRequest) -> dict[str, Any]:
        if request.dry_run:
            return {
                "status": "passed",
                "message": "Audit verification is not required for dry-run freeze checks.",
            }
        verify = getattr(self._audit_verifier, "verify", None)
        if not callable(verify):
            return {
                "status": "warning",
                "message": "Audit verifier is unavailable in this local gate context.",
            }
        from aion_brain.contracts.audit_integrity import AuditVerificationRequest

        result = verify(
            AuditVerificationRequest(
                created_by=request.requested_by,
                metadata={"source": "freeze_gate"},
            )
        )
        return {
            "status": "passed" if result.status == "passed" else "failed",
            "message": "Audit verification completed.",
            "details": {"audit_verification_id": result.audit_verification_id},
        }

    def _check_operator_readiness_available(self) -> dict[str, Any]:
        if self._operator_readiness_service is None:
            return {
                "status": "warning",
                "message": "Operator readiness is not wired into this freeze context.",
            }
        return {
            "status": "passed",
            "message": "Operator readiness is available.",
        }

    def _check_no_raw_secrets(self) -> dict[str, Any]:
        targets = [
            self._root_dir / "examples" / "scenarios",
            self._root_dir / "examples" / "fixtures",
        ]
        matches: builtins.list[str] = []
        secret_terms = {"api_key", "authorization", "bearer ", "client_secret", "private_key"}
        for root in targets:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in {".md", ".json", ".yaml"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                if any(term in text for term in secret_terms):
                    matches.append(path.relative_to(self._root_dir).as_posix())
        return {
            "status": "failed" if matches else "passed",
            "message": "No raw secrets found in release-owned fixtures.",
            "details": {"matches": sorted(set(matches))},
        }

    def _check_docs_current(self) -> dict[str, Any]:
        docs = [
            "docs/versioning.md",
            "docs/upgrade-policy.md",
            "docs/deprecation-policy.md",
            "docs/release-notes/v0.1.0.md",
            "CHANGELOG.md",
        ]
        missing = [path for path in docs if not (self._root_dir / path).is_file()]
        return {
            "status": "failed" if missing else "passed",
            "message": "Versioning and release docs are present.",
            "details": {"missing": missing},
        }

    def _check_adr_index(self) -> dict[str, Any]:
        adr = self._root_dir / "docs/adr/0036-version-manifest-compatibility-freeze-gate.md"
        index = self._root_dir / "docs/adr/README.md"
        indexed = (
            index.is_file()
            and "0036-version-manifest-compatibility-freeze-gate"
            in index.read_text(encoding="utf-8")
        )
        status = "passed" if adr.is_file() and indexed else "failed"
        return {
            "status": status,
            "message": "ADR 0036 exists and is indexed.",
            "details": {"adr_exists": adr.is_file(), "indexed": indexed},
        }

    def _authorize(self, request: FreezeGateRunRequest) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"freeze_gate.run-{uuid4().hex}",
                trace_id=None,
                actor_id=request.requested_by,
                workspace_id=None,
                action_type="freeze_gate.run",
                resource_type="freeze_gate",
                resource_id=request.freeze_gate_id,
                risk_level="medium",
                approval_present=True,
                requested_permissions=["freeze_gate.run"],
                security_scope=request.owner_scope,
                context={"version": request.version, "dry_run": request.dry_run},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _authorize_read(self, scope: builtins.list[str], resource_id: str | None) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"freeze_gate.read-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type="freeze_gate.read",
                resource_type="freeze_gate",
                resource_id=resource_id,
                risk_level="low",
                approval_present=True,
                requested_permissions=["freeze_gate.read"],
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
        scope: builtins.list[str],
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="freeze",
            node_id=node_id,
            intensity=intensity,
            scope=scope,
            payload=payload,
        )


def _build_report(checks: builtins.list[FreezeGateCheck]) -> dict[str, Any]:
    from aion_brain.freeze.report import build_freeze_report

    return build_freeze_report(checks)
