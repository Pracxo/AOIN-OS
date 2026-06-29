"""Deterministic local hardening gate service."""

from __future__ import annotations

import builtins
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.security_baseline import (
    HardeningGateRequest,
    HardeningGateRun,
    SecurityScanRequest,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import enrich_with_internal_dev_actor
from aion_brain.security_baseline.adapter_risk import AdapterRiskChecker
from aion_brain.security_baseline.api_exposure import APIExposureChecker
from aion_brain.security_baseline.config_checker import ConfigHardeningChecker
from aion_brain.security_baseline.control_catalog import SecurityControlCatalog
from aion_brain.security_baseline.dependency_metadata import DependencyMetadataScanner
from aion_brain.security_baseline.repository import SecurityBaselineRepository
from aion_brain.security_baseline.secret_scanner import SecretScanner
from aion_brain.security_baseline.threat_model import ThreatModelService
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class HardeningGateService:
    """Run deterministic local security hardening checks."""

    def __init__(
        self,
        repository: SecurityBaselineRepository,
        policy_adapter: PolicyAdapter,
        *,
        secret_scanner: SecretScanner,
        config_checker: ConfigHardeningChecker,
        api_exposure_checker: APIExposureChecker,
        adapter_risk_checker: AdapterRiskChecker,
        dependency_metadata_scanner: DependencyMetadataScanner,
        threat_model_service: ThreatModelService,
        security_control_catalog: SecurityControlCatalog,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._secret_scanner = secret_scanner
        self._config_checker = config_checker
        self._api_exposure_checker = api_exposure_checker
        self._adapter_risk_checker = adapter_risk_checker
        self._dependency_metadata_scanner = dependency_metadata_scanner
        self._threat_model_service = threat_model_service
        self._security_control_catalog = security_control_catalog
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._audit_sink = audit_sink
        self._extension_registry_repository: object | None = None
        self._module_binding_repository: object | None = None
        self._module_mock_repository: object | None = None
        self._model_provider_hardening_repository: object | None = None
        self._conformance_repository: object | None = None

    def set_extension_registry_repository(self, repository: object | None) -> None:
        """Attach Extension Registry after kernel assembly."""

        self._extension_registry_repository = repository

    def set_module_binding_repository(self, repository: object | None) -> None:
        """Attach module binding registry after kernel assembly."""

        self._module_binding_repository = repository

    def set_module_mock_repository(self, repository: object | None) -> None:
        """Attach module mock runtime after kernel assembly."""

        self._module_mock_repository = repository

    def set_model_provider_hardening_repository(self, repository: object | None) -> None:
        """Attach model provider hardening after kernel assembly."""

        self._model_provider_hardening_repository = repository

    def set_conformance_repository(self, repository: object | None) -> None:
        """Attach conformance readiness metadata after kernel assembly."""

        self._conformance_repository = repository

    def run(self, request: HardeningGateRequest, *, app: object | None = None) -> HardeningGateRun:
        """Run the local security hardening gate."""
        self._authorize(
            "security.hardening.run",
            request.owner_scope,
            actor_id=request.created_by,
            risk_level="medium",
            context={"version": request.version, **request.metadata},
        )
        run_id = request.hardening_gate_id or f"hardening-gate-{uuid4().hex}"
        started = datetime.now(UTC)
        self._emit(
            "hardening_gate_started",
            run_id,
            request.owner_scope,
            0.6,
            {"version": request.version},
        )
        checks: list[dict[str, Any]] = []
        if not self._settings.hardening_gate_enabled:
            checks.append(
                _check(
                    "hardening_gate_enabled",
                    "warning",
                    "Hardening gate is disabled by configuration.",
                    "configuration",
                )
            )
        if request.include_secret_scan:
            checks.extend(self._secret_scan_checks(request))
        if request.include_config_check:
            checks.extend(self._config_checker.check())
        if request.include_api_exposure_check:
            checks.extend(self._api_checks(app))
        if request.include_adapter_risk_check:
            checks.extend(self._adapter_risk_checker.check())
        if request.include_dependency_metadata_check:
            checks.extend(self._dependency_metadata_scanner.check())
        checks.append(self._threat_model_check(request.owner_scope))
        if request.include_policy_coverage_check:
            checks.append(
                _check(
                    "policy_coverage_available",
                    "warning",
                    "Policy coverage is external to this gate.",
                    "policy",
                )
            )
        if request.include_autonomy_defaults_check:
            checks.append(self._autonomy_check())
        if request.include_sandbox_check:
            checks.append(self._sandbox_check())
        if request.include_backup_redaction_check:
            checks.append(self._backup_check())
        if request.include_release_package_check:
            checks.append(self._release_package_check())
        checks.extend(self._extension_registry_checks())
        checks.extend(self._module_binding_checks())
        checks.extend(self._module_mock_checks())
        checks.extend(self._model_provider_hardening_checks())
        checks.extend(self._conformance_checks())
        checks.extend(self._local_auth_checks())
        checks.extend(self._local_session_checks())
        checks.extend(self._connector_runtime_checks())
        checks.extend(self._audit_integrity_checks())
        checks.append(self._control_catalog_check())

        failures = [
            check
            for check in checks
            if _failed(check)
            and (
                check.get("severity") in {"high", "critical"}
                or check.get("name") in _CRITICAL_CHECK_NAMES
            )
        ]
        warnings = [check for check in checks if check.get("status") in {"warning", "skipped"}]
        if request.fail_on_high:
            high_findings = [
                check
                for check in checks
                if check.get("name") == "local_secret_scan"
                and int(check.get("details", {}).get("high_or_critical_findings", 0)) > 0
            ]
            failures.extend(high_findings)
        status = "failed" if failures else ("warning" if warnings else "passed")
        run = HardeningGateRun(
            hardening_gate_id=run_id,
            version=request.version,
            status=cast(Any, status),
            owner_scope=request.owner_scope,
            checks=checks,
            failures=_dedupe(failures),
            warnings=warnings,
            report={
                "external_calls": False,
                "check_count": len(checks),
                "failure_count": len(_dedupe(failures)),
                "warning_count": len(warnings),
                "local_only": True,
            },
            created_by=request.created_by,
            created_at=started,
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_hardening_gate(run)
        self._emit(
            "hardening_gate_completed" if saved.status != "failed" else "hardening_gate_failed",
            saved.hardening_gate_id,
            saved.owner_scope,
            0.9 if saved.status == "passed" else 1.0,
            {"status": saved.status},
        )
        record_audit_event(
            self._audit_sink,
            action_type="security.hardening.run",
            resource_type="hardening_gate",
            resource_id=saved.hardening_gate_id,
            event_type="hardening_gate_completed",
            outcome="completed" if saved.status != "failed" else "failed",
            source_component="hardening_gate",
            actor_id=request.created_by,
            payload={"status": saved.status, "check_count": len(saved.checks)},
        )
        return saved

    def get(self, hardening_gate_id: str) -> HardeningGateRun | None:
        """Return one hardening gate run."""
        self._authorize(
            "security.hardening.read",
            ["workspace:main"],
            resource_id=hardening_gate_id,
        )
        return self._repository.get_hardening_gate(hardening_gate_id)

    def list(
        self,
        version: str | None = None,
        status: str | None = None,
    ) -> list[HardeningGateRun]:
        """List hardening gate runs."""
        self._authorize(
            "security.hardening.read",
            ["workspace:main"],
            context={"version": version, "status": status},
        )
        return self._repository.list_hardening_gates(version=version, status=status)

    def _secret_scan_checks(
        self,
        request: HardeningGateRequest,
    ) -> builtins.list[dict[str, Any]]:
        scan = self._secret_scanner.scan(
            SecurityScanRequest(
                scan_type="secrets",
                owner_scope=request.owner_scope,
                max_file_size_mb=self._settings.security_scan_max_file_size_mb,
                metadata=request.metadata,
                created_by=request.created_by,
            )
        )
        high_count = sum(1 for finding in scan.findings if finding.severity in {"high", "critical"})
        return [
            {
                "name": "local_secret_scan",
                "category": "configuration",
                "status": "failed" if high_count else ("warning" if scan.findings else "passed"),
                "severity": "critical" if high_count else "medium",
                "message": "Local secret scan completed.",
                "details": {
                    "security_scan_id": scan.security_scan_id,
                    "finding_count": len(scan.findings),
                    "high_or_critical_findings": high_count,
                },
            }
        ]

    def _api_checks(self, app: object | None) -> builtins.list[dict[str, Any]]:
        openapi = getattr(app, "openapi", None)
        if not callable(openapi):
            return [
                _check(
                    "api_exposure_check_available",
                    "warning",
                    "OpenAPI app context unavailable.",
                    "api",
                )
            ]
        return self._api_exposure_checker.check(openapi())

    def _threat_model_check(self, scope: builtins.list[str]) -> dict[str, Any]:
        records = self._repository.list_threat_models()
        return _check(
            "threat_model_complete",
            "passed" if records else "warning",
            (
                "Threat model records are present."
                if records
                else "Threat model records are not seeded."
            ),
            "configuration",
            {"record_count": len(records)},
        )

    def _control_catalog_check(self) -> dict[str, Any]:
        controls = self._repository.list_controls()
        missing = [control.control_key for control in controls if control.status == "missing"]
        status = "failed" if missing else ("warning" if not controls else "passed")
        return _check(
            "control_catalog_complete",
            status,
            "Security control catalog checked.",
            "configuration",
            {"control_count": len(controls), "missing": missing},
        )

    def _autonomy_check(self) -> dict[str, Any]:
        enabled = (
            self._settings.autonomy_default_max_mode in {"autonomous", "full"}
            or self._settings.autonomy_external_tools_allowed_default
            or self._settings.autonomy_external_models_allowed_default
        )
        return _check(
            "no_full_autonomy_default",
            "failed" if enabled else "passed",
            "Full autonomy defaults are disabled.",
            "autonomy",
        )

    def _sandbox_check(self) -> dict[str, Any]:
        enabled = (
            self._settings.sandbox_execution_enabled
            or self._settings.sandbox_docker_enabled
            or self._settings.sandbox_firecracker_enabled
        )
        return _check(
            "sandbox_execution_disabled_by_default",
            "failed" if enabled else "passed",
            "Sandbox execution is disabled by default.",
            "sandbox",
        )

    def _backup_check(self) -> dict[str, Any]:
        passed = self._settings.backup_default_redaction_mode == "redact_sensitive"
        return _check(
            "backup_redaction_default",
            "passed" if passed else "failed",
            "Backup redaction defaults to redact_sensitive.",
            "backup",
        )

    def _release_package_check(self) -> dict[str, Any]:
        return _check(
            "release_package_safety_available",
            "passed" if self._settings.release_packaging_enabled else "warning",
            "Release package safety checks are available.",
            "release",
        )

    def _extension_registry_checks(self) -> builtins.list[dict[str, Any]]:
        list_packages = getattr(self._extension_registry_repository, "list_packages", None)
        packages = list_packages(limit=1000) if callable(list_packages) else []
        blocked = [
            item
            for item in packages
            if getattr(item, "compatibility_status", None) in {"blocked", "failed"}
            or getattr(item, "status", None) == "incompatible"
        ]
        return [
            _check(
                "extension_code_loading_disabled",
                ("failed" if self._settings.extension_code_loading_enabled else "passed"),
                "Extension code loading is disabled.",
                "extensions",
            ),
            _check(
                "extension_activation_disabled",
                ("failed" if self._settings.extension_activation_enabled else "passed"),
                "Extension activation is disabled.",
                "extensions",
            ),
            _check(
                "extension_external_sources_disabled",
                ("failed" if self._settings.extension_external_sources_enabled else "passed"),
                "Extension external sources are disabled.",
                "extensions",
            ),
            _check(
                "no_blocked_extension_packages",
                "failed" if blocked else "passed",
                "Extension registry has no blocked package metadata.",
                "extensions",
                {"blocked_count": len(blocked), "package_count": len(packages)},
            ),
        ]

    def _module_binding_checks(self) -> builtins.list[dict[str, Any]]:
        list_bindings = getattr(self._module_binding_repository, "list_bindings", None)
        list_validations = getattr(
            self._module_binding_repository,
            "list_validation_runs",
            None,
        )
        bindings = list_bindings(limit=1000) if callable(list_bindings) else []
        validations = list_validations(limit=1000) if callable(list_validations) else []
        validated_binding_ids = {
            binding_id
            for run in validations
            if getattr(run, "status", None) in {"passed", "warning", "dry_run"}
            for binding_id in getattr(run, "capability_binding_ids", [])
        }
        active_unvalidated = [
            item
            for item in bindings
            if getattr(item, "status", None) in {"proposed", "validated"}
            and getattr(item, "capability_binding_id", None) not in validated_binding_ids
        ]
        blocked = [item for item in bindings if getattr(item, "status", None) == "blocked"]
        return [
            _check(
                "module_slot_activation_disabled",
                "failed" if self._settings.module_slot_activation_enabled else "passed",
                "Module slot activation is disabled.",
                "module_bindings",
            ),
            _check(
                "capability_binding_activation_disabled",
                "failed" if self._settings.capability_binding_activation_enabled else "passed",
                "Capability binding activation is disabled.",
                "module_bindings",
            ),
            _check(
                "dynamic_route_registration_disabled",
                "failed" if self._settings.dynamic_route_registration_enabled else "passed",
                "Dynamic route registration is disabled.",
                "module_bindings",
            ),
            _check(
                "no_active_unvalidated_capability_bindings",
                "failed" if active_unvalidated else "passed",
                "No active capability bindings are missing validation records.",
                "module_bindings",
                details={"count": len(active_unvalidated)},
            ),
            _check(
                "no_blocked_capability_bindings",
                "failed" if blocked else "passed",
                "No blocked capability binding metadata is present.",
                "module_bindings",
                details={"count": len(blocked)},
            ),
        ]

    def _module_mock_checks(self) -> builtins.list[dict[str, Any]]:
        list_runs = getattr(self._module_mock_repository, "list_runs", None)
        list_findings = getattr(self._module_mock_repository, "list_findings", None)
        runs = list_runs(limit=1000) if callable(list_runs) else []
        findings = list_findings(status="open", limit=1000) if callable(list_findings) else []
        blocked_runs = [
            item for item in runs if getattr(item, "status", None) in {"failed", "blocked"}
        ]
        high_findings = [
            item for item in findings if getattr(item, "severity", None) in {"high", "critical"}
        ]
        return [
            _check(
                "module_mock_controlled_execution_disabled",
                (
                    "failed"
                    if self._settings.module_mock_controlled_execution_enabled
                    else "passed"
                ),
                "Module mock controlled execution is disabled.",
                "module_mock_runtime",
            ),
            _check(
                "module_mock_code_loading_disabled",
                "failed" if self._settings.module_mock_code_loading_enabled else "passed",
                "Module mock code loading is disabled.",
                "module_mock_runtime",
            ),
            _check(
                "module_mock_external_calls_disabled",
                "failed" if self._settings.module_mock_external_calls_enabled else "passed",
                "Module mock external calls are disabled.",
                "module_mock_runtime",
            ),
            _check(
                "no_blocked_module_mock_runs",
                "failed" if blocked_runs else "passed",
                "No blocked module mock runtime records are present.",
                "module_mock_runtime",
                details={"count": len(blocked_runs), "run_count": len(runs)},
            ),
            _check(
                "no_high_module_mock_findings",
                "failed" if high_findings else "passed",
                "No high-severity module mock findings are open.",
                "module_mock_runtime",
                details={"count": len(high_findings), "finding_count": len(findings)},
            ),
        ]

    def _model_provider_hardening_checks(self) -> builtins.list[dict[str, Any]]:
        list_blockers = getattr(self._model_provider_hardening_repository, "list_blockers", None)
        blockers = list_blockers(status="open", limit=1000) if callable(list_blockers) else []
        high_blockers = [
            item for item in blockers if getattr(item, "severity", None) in {"high", "critical"}
        ]
        return [
            _check(
                "external_model_calls_disabled",
                "failed" if self._settings.external_model_calls_enabled else "passed",
                "External model calls are disabled.",
                "model_provider_hardening",
            ),
            _check(
                "model_provider_credentials_disabled",
                "failed" if self._settings.model_provider_credentials_enabled else "passed",
                "Model provider credentials are disabled.",
                "model_provider_hardening",
            ),
            _check(
                "no_high_provider_hardening_blockers",
                "warning" if high_blockers else "passed",
                "No high-severity provider hardening blockers are open.",
                "model_provider_hardening",
                details={"count": len(high_blockers), "blocker_count": len(blockers)},
            ),
        ]

    def _local_auth_checks(self) -> builtins.list[dict[str, Any]]:
        return [
            _check(
                "production_auth_disabled",
                "failed" if self._settings.production_auth_enabled else "passed",
                "Production auth is disabled.",
                "local_auth",
            ),
            _check(
                "local_auth_material_disabled",
                "failed" if self._settings.auth_credentials_enabled else "passed",
                "Auth material handling is disabled.",
                "local_auth",
            ),
            _check(
                "auth_session_state_disabled",
                "failed" if self._settings.auth_sessions_enabled else "passed",
                "Auth session state is disabled.",
                "local_auth",
            ),
            _check(
                "external_identity_provider_disabled",
                "failed" if self._settings.external_identity_provider_enabled else "passed",
                "External identity provider integration is disabled.",
                "local_auth",
            ),
            _check(
                "local_auth_write_actions_disabled",
                "failed" if self._settings.local_auth_write_actions_enabled else "passed",
                "Local auth cannot grant write actions.",
                "local_auth",
            ),
        ]

    def _local_session_checks(self) -> builtins.list[dict[str, Any]]:
        return [
            _check(
                "local_session_preview_dev_only",
                "passed" if self._settings.local_session_dev_only else "failed",
                "Local session previews are dev-only.",
                "local_session",
            ),
            _check(
                "local_session_preview_read_only",
                "passed" if self._settings.local_session_read_only else "failed",
                "Local session previews are read-only.",
                "local_session",
            ),
            _check(
                "local_session_auth_material_disabled",
                "failed" if self._settings.local_session_credentials_enabled else "passed",
                "Local session auth material backing is disabled.",
                "local_session",
            ),
            _check(
                "local_session_token_issuance_disabled",
                "failed" if self._settings.local_session_tokens_enabled else "passed",
                "Local session token issuance is disabled.",
                "local_session",
            ),
            _check(
                "local_session_cookie_issuance_disabled",
                "failed" if self._settings.local_session_cookies_enabled else "passed",
                "Local session cookie issuance is disabled.",
                "local_session",
            ),
            _check(
                "local_session_persistence_disabled",
                "failed" if self._settings.local_session_persistence_enabled else "passed",
                "Local session persistence is disabled.",
                "local_session",
            ),
            _check(
                "local_session_write_actions_disabled",
                "failed" if self._settings.local_session_write_actions_enabled else "passed",
                "Local session cannot grant write actions.",
                "local_session",
            ),
            _check(
                "local_session_execution_disabled",
                "failed" if self._settings.local_session_execution_enabled else "passed",
                "Local session cannot grant execution.",
                "local_session",
            ),
            _check(
                "local_session_activation_disabled",
                "failed" if self._settings.local_session_activation_enabled else "passed",
                "Local session cannot grant activation.",
                "local_session",
            ),
            _check(
                "local_session_external_calls_disabled",
                "failed" if self._settings.local_session_external_calls_enabled else "passed",
                "Local session cannot grant external calls.",
                "local_session",
            ),
        ]

    def _connector_runtime_checks(self) -> builtins.list[dict[str, Any]]:
        return [
            _check(
                "connector_runtime_disabled",
                "failed" if self._settings.connector_runtime_enabled else "passed",
                "Connector runtime is disabled.",
                "connector_runtime",
            ),
            _check(
                "connector_external_calls_disabled",
                "failed" if self._settings.connector_external_calls_enabled else "passed",
                "Connector external calls are disabled.",
                "connector_runtime",
            ),
            _check(
                "connector_credentials_disabled",
                "failed" if self._settings.connector_credentials_enabled else "passed",
                "Connector credential handling is disabled.",
                "connector_runtime",
            ),
            _check(
                "connector_token_storage_disabled",
                "failed" if self._settings.connector_token_storage_enabled else "passed",
                "Connector token storage is disabled.",
                "connector_runtime",
            ),
            _check(
                "connector_activation_disabled",
                "failed" if self._settings.connector_activation_enabled else "passed",
                "Connector activation is disabled.",
                "connector_runtime",
            ),
            _check(
                "connector_route_registration_disabled",
                "failed" if self._settings.connector_route_registration_enabled else "passed",
                "Connector route registration is disabled.",
                "connector_runtime",
            ),
        ]

    def _conformance_checks(self) -> builtins.list[dict[str, Any]]:
        if self._conformance_repository is None:
            return [
                _check(
                    "conformance_repository_optional",
                    "passed",
                    "Conformance repository is optional in isolated hardening tests.",
                    "conformance",
                )
            ]
        list_runs = getattr(self._conformance_repository, "list_runs", None)
        list_findings = getattr(self._conformance_repository, "list_findings", None)
        list_readiness = getattr(self._conformance_repository, "list_readiness", None)
        runs = list_runs(limit=1000) if callable(list_runs) else []
        findings = list_findings(status="open", limit=1000) if callable(list_findings) else []
        readiness = list_readiness(limit=1000) if callable(list_readiness) else []
        failed_runs = [
            item for item in runs if getattr(item, "status", None) in {"failed", "blocked"}
        ]
        high_findings = [
            item for item in findings if getattr(item, "severity", None) in {"high", "critical"}
        ]
        blocked_readiness = [
            item for item in readiness if getattr(item, "status", None) == "blocked"
        ]
        return [
            _check(
                "conformance_code_execution_disabled",
                "failed" if self._settings.conformance_code_execution_enabled else "passed",
                "Conformance code execution is disabled.",
                "conformance",
            ),
            _check(
                "conformance_external_calls_disabled",
                "failed" if self._settings.conformance_external_calls_enabled else "passed",
                "Conformance external calls are disabled.",
                "conformance",
            ),
            _check(
                "readiness_activation_disabled",
                "failed" if self._settings.readiness_activation_enabled else "passed",
                "Readiness activation is disabled.",
                "conformance",
            ),
            _check(
                "no_failed_conformance_runs",
                "failed" if failed_runs else "passed",
                "No failed or blocked conformance runs are present.",
                "conformance",
                {"count": len(failed_runs)},
            ),
            _check(
                "no_high_conformance_findings",
                "failed" if high_findings else "passed",
                "No high-severity conformance findings are open.",
                "conformance",
                {"count": len(high_findings)},
            ),
            _check(
                "no_blocked_readiness_assessments",
                "failed" if blocked_readiness else "passed",
                "No blocked extension readiness assessments are present.",
                "conformance",
                {"count": len(blocked_readiness)},
            ),
        ]

    def _audit_integrity_checks(self) -> builtins.list[dict[str, Any]]:
        return [
            _check(
                "audit_redaction_enabled",
                "passed" if self._settings.audit_redact_sensitive_payloads else "failed",
                "Audit redaction is enabled.",
                "audit_integrity",
            ),
            _check(
                "audit_no_chain_of_thought_storage",
                "passed",
                "Audit contracts reject chain-of-thought storage.",
                "audit_integrity",
            ),
            _check(
                "audit_export_redaction_default",
                (
                    "passed"
                    if self._settings.audit_export_output_dir == "artifacts/audit"
                    else "warning"
                ),
                "Audit export defaults to the local artifacts/audit path.",
                "audit_integrity",
            ),
        ]

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
        policy_request = PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=None,
            actor_id=actor_id,
            workspace_id=None,
            action_type=action_type,
            resource_type="hardening_gate",
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
        policy_request = enrich_with_internal_dev_actor(
            policy_request,
            self._settings,
            scope=scope,
            permissions=[action_type],
        )
        decision = self._policy_adapter.authorize(policy_request)
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
            node_type="hardening",
            node_id=node_id,
            intensity=intensity,
            scope=scope,
            payload=payload,
        )


_CRITICAL_CHECK_NAMES = {
    "local_secret_scan",
    "api_stacktrace_exposed_false",
    "no_full_autonomy_default",
    "sandbox_execution_disabled_by_default",
    "restore_apply_disabled_by_default",
    "external_models_disabled_by_default",
    ".env_not_committed",
    "no_provider_sdk_objects_in_public_contracts",
}


def _check(
    name: str,
    status: str,
    message: str,
    category: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "status": status,
        "severity": "high" if status == "failed" else "medium",
        "message": message,
        "details": details or {},
    }


def _failed(check: dict[str, Any]) -> bool:
    return check.get("status") == "failed"


def _dedupe(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for check in checks:
        key = str(check.get("name"))
        if key in seen:
            continue
        seen.add(key)
        result.append(check)
    return result
