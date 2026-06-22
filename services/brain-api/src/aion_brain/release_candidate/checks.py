"""Release candidate verification check collection and normalization."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.freeze import FreezeGateRunRequest
from aion_brain.contracts.golden_path import GoldenPathRunRequest
from aion_brain.contracts.operator import OperatorOverviewRequest
from aion_brain.contracts.release_candidate import RCGateRunRequest
from aion_brain.contracts.release_package import ReleasePackageRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.security_baseline import HardeningGateRequest
from aion_brain.contracts.setup_doctor import SetupDoctorRequest
from aion_brain.contracts.verification_matrix import (
    VerificationCheck,
    VerificationCheckStatus,
    VerificationCheckType,
    VerificationSeverity,
)
from aion_brain.release_candidate.hash import hash_check_evidence
from aion_brain.release_candidate.redaction import safe_rc_summary

_CHECK_TYPES: dict[str, VerificationCheckType] = {
    "tests.brain": "unit_tests",
    "tests.sdk": "sdk_tests",
    "lint": "lint",
    "typecheck": "typecheck",
    "no_domain_drift": "domain_drift",
    "boundary_check": "boundary",
    "policy_coverage": "policy_coverage",
    "openapi_hygiene": "openapi",
    "repo_health": "repo_health",
    "docker_compose_config": "docker_config",
    "docker_smoke_live": "docker_smoke",
    "health_readiness": "health_readiness",
    "bootstrap_doctor": "bootstrap",
    "golden_path": "golden_path",
    "release_smoke": "release_smoke",
    "freeze_gate": "freeze_gate",
    "release_package_dry_run": "release_package",
    "contract_registry": "contract_registry",
    "resource_registry": "resource_registry",
    "lifecycle_safety": "lifecycle",
    "extension_safety": "extension",
    "module_binding_safety": "module_binding",
    "conformance_safety": "conformance",
    "security_baseline": "security",
    "runtime_config_safe": "runtime_config",
    "operator_overview": "operator",
    "rc_evidence_pack": "generic",
}


class VerificationCheckCollector:
    """Collect service-level checks without spawning shell commands."""

    def __init__(
        self,
        *,
        setup_doctor: object | None = None,
        golden_path_runner: object | None = None,
        release_smoke: object | None = None,
        freeze_gate_service: object | None = None,
        release_packager: object | None = None,
        contract_registry_repository: object | None = None,
        contract_registry_report_service: object | None = None,
        resource_registry_validator: object | None = None,
        lifecycle_service: object | None = None,
        extension_registry_repository: object | None = None,
        module_binding_repository: object | None = None,
        conformance_repository: object | None = None,
        hardening_gate_service: object | None = None,
        runtime_config_status_service: object | None = None,
        operator_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._setup_doctor = setup_doctor
        self._golden_path_runner = golden_path_runner
        self._release_smoke = release_smoke
        self._freeze_gate_service = freeze_gate_service
        self._release_packager = release_packager
        self._contract_registry_repository = contract_registry_repository
        self._contract_registry_report_service = contract_registry_report_service
        self._resource_registry_validator = resource_registry_validator
        self._lifecycle_service = lifecycle_service
        self._extension_registry_repository = extension_registry_repository
        self._module_binding_repository = module_binding_repository
        self._conformance_repository = conformance_repository
        self._hardening_gate_service = hardening_gate_service
        self._runtime_config_status_service = runtime_config_status_service
        self._operator_service = operator_service
        self._settings = settings or get_settings()

    def collect_service_checks(self, request: RCGateRunRequest) -> list[VerificationCheck]:
        """Collect safe service checks for the RC gate."""

        checks: list[VerificationCheck] = []
        if request.include_bootstrap:
            checks.append(self._bootstrap_check(request))
        if request.include_golden_path:
            checks.append(self._golden_path_check(request))
        if request.include_release_package:
            checks.append(self._release_smoke_check(request))
        if request.include_freeze_gate:
            checks.append(self._freeze_gate_check(request))
        if request.include_release_package:
            checks.append(self._release_package_check(request))
        checks.extend(
            [
                self._contract_registry_check(request),
                self._resource_registry_check(request),
                self._lifecycle_check(request),
                self._extension_check(request),
                self._module_binding_check(request),
                self._conformance_check(request),
                self._security_baseline_check(request),
                self._runtime_config_check(request),
                self._operator_check(request),
            ]
        )
        if request.include_docker_smoke:
            checks.append(
                self.build_check(
                    "docker_smoke_live",
                    "warning",
                    {"message": "Docker smoke must be supplied by local scripts."},
                    required=False,
                    summary="Docker smoke was not run inside Brain service.",
                )
            )
        return checks

    def normalize_script_result(self, check_key: str, payload: dict[str, Any]) -> VerificationCheck:
        """Normalize one local script result supplied by scripts."""

        if check_key not in _CHECK_TYPES:
            return self.build_check(
                check_key="unknown_check",
                status="failed",
                evidence={"source_check_key": check_key, "payload": payload},
                summary="Unknown verification check failed closed.",
                required=True,
            )
        status = str(payload.get("status") or ("passed" if payload.get("passed") else "failed"))
        required = bool(payload.get("required", True))
        summary = str(payload.get("summary") or payload.get("message") or f"{check_key} result")
        return self.build_check(
            check_key,
            status,
            payload,
            required=required,
            duration_ms=_int_or_none(payload.get("duration_ms")),
            command_hint=payload.get("command_hint")
            if isinstance(payload.get("command_hint"), str)
            else None,
            summary=summary,
        )

    def build_check(
        self,
        check_key: str,
        status: str,
        evidence: dict[str, Any],
        *,
        required: bool = True,
        summary: str | None = None,
        title: str | None = None,
        command_hint: str | None = None,
        duration_ms: int | None = None,
    ) -> VerificationCheck:
        """Build a normalized check with deterministic metadata."""

        normalized_status = _normalize_check_status(status)
        safe_evidence = safe_rc_summary(evidence)
        severity = _severity_for(normalized_status, required)
        return VerificationCheck(
            verification_check_id=f"rc-check-{uuid4().hex}",
            check_key=check_key,
            check_type=_CHECK_TYPES.get(check_key, "generic"),
            status=normalized_status,
            severity=severity,
            required=required,
            passed=normalized_status == "passed",
            title=title or _title_for(check_key),
            summary=summary or _summary_for(check_key, normalized_status),
            command_hint=command_hint,
            evidence=safe_evidence,
            duration_ms=duration_ms,
            error={} if normalized_status not in {"failed", "blocked"} else safe_evidence,
            metadata={
                "evidence_hash": hash_check_evidence(safe_evidence),
                "external_calls": False,
                "source_mutation": False,
            },
            created_at=datetime.now(UTC),
        )

    def _bootstrap_check(self, request: RCGateRunRequest) -> VerificationCheck:
        run = getattr(self._setup_doctor, "run", None)
        if callable(run):
            try:
                result = run(
                    SetupDoctorRequest(
                        trace_id=request.trace_id,
                        actor_id=request.actor_id,
                        workspace_id=request.workspace_id,
                        owner_scope=request.owner_scope,
                        include_golden_path=False,
                        include_release_smoke=False,
                        create_findings=False,
                        create_notifications=False,
                        metadata={"source": "rc_gate"},
                        created_by=request.created_by,
                    )
                )
                status = "passed" if getattr(result, "local_ready", False) else "warning"
                if getattr(result, "status", "") == "failed":
                    status = "failed"
                return self.build_check(
                    "bootstrap_doctor",
                    status,
                    _jsonable(result),
                    summary="Setup doctor contributed local readiness.",
                )
            except Exception as exc:
                return self._exception_check("bootstrap_doctor", exc)
        return self._missing_check("bootstrap_doctor")

    def _golden_path_check(self, request: RCGateRunRequest) -> VerificationCheck:
        run = getattr(self._golden_path_runner, "run", None)
        if callable(run):
            try:
                result = run(
                    GoldenPathRunRequest(
                        trace_id=request.trace_id,
                        actor_id=request.actor_id,
                        workspace_id=request.workspace_id,
                        mode="dry_run",
                        owner_scope=request.owner_scope,
                        run_all_defaults=True,
                        create_notifications=False,
                        create_operator_items=False,
                        include_release_smoke=False,
                        metadata={"source": "rc_gate", "external_calls": False},
                        created_by=request.created_by,
                    )
                )
                return self.build_check(
                    "golden_path",
                    _status_from_result(result, pass_values={"passed", "dry_run", "completed"}),
                    _jsonable(result),
                    summary="Golden path dry-run contributed readiness.",
                )
            except Exception as exc:
                return self._exception_check("golden_path", exc)
        return self._status_repository_check("golden_path", self._golden_path_runner)

    def _release_smoke_check(self, request: RCGateRunRequest) -> VerificationCheck:
        run = getattr(self._release_smoke, "run", None)
        if callable(run):
            try:
                result = run(request.owner_scope, created_by=request.created_by)
                return self.build_check(
                    "release_smoke",
                    _status_from_result(result, pass_values={"passed", "dry_run", "completed"}),
                    _jsonable(result),
                    summary="Release smoke matrix contributed readiness.",
                )
            except Exception as exc:
                return self._exception_check("release_smoke", exc)
        return self._missing_check("release_smoke")

    def _freeze_gate_check(self, request: RCGateRunRequest) -> VerificationCheck:
        run = getattr(self._freeze_gate_service, "run", None)
        if callable(run):
            try:
                result = run(
                    FreezeGateRunRequest(
                        version=request.version or self._settings.version,
                        requested_by=request.created_by,
                        owner_scope=request.owner_scope,
                        include_contract_export=False,
                        include_release_baseline=False,
                        include_kernel_self_test=False,
                        include_policy_coverage=False,
                        include_openapi_hygiene=False,
                        include_boundary_check=False,
                        include_no_domain_drift=False,
                        include_repo_health=False,
                        dry_run=True,
                        metadata={"source": "rc_gate"},
                    )
                )
                return self.build_check(
                    "freeze_gate",
                    _freeze_gate_status_from_result(result),
                    _jsonable(result),
                    summary="Freeze gate dry-run contributed readiness.",
                )
            except Exception as exc:
                return self._exception_check("freeze_gate", exc)
        return self._missing_check("freeze_gate")

    def _release_package_check(self, request: RCGateRunRequest) -> VerificationCheck:
        package = getattr(self._release_packager, "package", None)
        if callable(package):
            try:
                result = package(
                    ReleasePackageRequest(
                        version=request.version or self._settings.version,
                        created_by=request.created_by,
                        owner_scope=request.owner_scope,
                        include_release_baseline=False,
                        include_freeze_gate=False,
                        dry_run=True,
                        metadata={"source": "rc_gate"},
                    )
                )
                return self.build_check(
                    "release_package_dry_run",
                    _status_from_result(result, pass_values={"dry_run", "passed", "created"}),
                    _jsonable(result),
                    summary="Release package dry-run contributed readiness.",
                )
            except Exception as exc:
                return self._exception_check("release_package_dry_run", exc)
        return self._missing_check("release_package_dry_run")

    def _contract_registry_check(self, request: RCGateRunRequest) -> VerificationCheck:
        latest_scan = _safe_call(self._contract_registry_repository, "latest_scan")
        report = _safe_call(self._contract_registry_report_service, "generate", request.owner_scope)
        evidence = {"latest_scan": _jsonable(latest_scan), "report": _jsonable(report)}
        if _has_breaking_finding(evidence):
            return self.build_check(
                "contract_registry",
                "blocked",
                evidence,
                summary="Contract Registry has breaking findings.",
            )
        return self.build_check(
            "contract_registry",
            "passed",
            evidence,
            summary="Contract Registry has no breaking blocker.",
        )

    def _resource_registry_check(self, request: RCGateRunRequest) -> VerificationCheck:
        validate = getattr(self._resource_registry_validator, "validate", None)
        result = None
        if callable(validate):
            try:
                result = validate(request.owner_scope, dry_run=True)
            except TypeError:
                result = _safe_call(
                    self._resource_registry_validator, "validate", request.owner_scope
                )
            except Exception as exc:
                return self._exception_check("resource_registry", exc)
        evidence = _jsonable(result) or {
            "status": "not_configured",
            "critical_markers_present": False,
        }
        if _has_critical_marker(evidence):
            return self.build_check(
                "resource_registry",
                "blocked",
                evidence,
                summary="Resource Registry has critical broken references.",
            )
        return self.build_check(
            "resource_registry",
            "passed",
            evidence,
            summary="Resource Registry validation has no critical blocker.",
        )

    def _lifecycle_check(self, request: RCGateRunRequest) -> VerificationCheck:
        evidence = {
            "hard_delete_enabled": bool(
                getattr(self._settings, "lifecycle_hard_delete_enabled", False)
            ),
            "purge_preview_allowed": bool(
                getattr(self._settings, "lifecycle_purge_preview_apply_enabled", False)
            ),
            "status": _jsonable(_safe_call(self._lifecycle_service, "status", request.owner_scope)),
        }
        if evidence["hard_delete_enabled"] or evidence["purge_preview_allowed"]:
            return self.build_check(
                "lifecycle_safety",
                "blocked",
                evidence,
                summary="Lifecycle hard-delete risk blocks RC.",
            )
        return self.build_check(
            "lifecycle_safety", "passed", evidence, summary="Lifecycle remains non-destructive."
        )

    def _extension_check(self, request: RCGateRunRequest) -> VerificationCheck:
        evidence = {
            "code_loading_enabled": self._settings.extension_code_loading_enabled,
            "activation_enabled": self._settings.extension_activation_enabled,
            "external_sources_enabled": self._settings.extension_external_sources_enabled,
            "status": _jsonable(
                _safe_call(self._extension_registry_repository, "status", request.owner_scope)
            ),
        }
        if any(
            bool(evidence[key])
            for key in ("code_loading_enabled", "activation_enabled", "external_sources_enabled")
        ):
            return self.build_check(
                "extension_safety",
                "blocked",
                evidence,
                summary="Extension execution features are enabled.",
            )
        return self.build_check(
            "extension_safety",
            "passed",
            evidence,
            summary="Extension activation and code loading remain disabled.",
        )

    def _module_binding_check(self, request: RCGateRunRequest) -> VerificationCheck:
        evidence = {
            "module_slot_activation_enabled": self._settings.module_slot_activation_enabled,
            "capability_binding_activation_enabled": (
                self._settings.capability_binding_activation_enabled
            ),
            "dynamic_route_registration_enabled": self._settings.dynamic_route_registration_enabled,
            "status": _jsonable(
                _safe_call(self._module_binding_repository, "status", request.owner_scope)
            ),
        }
        if any(
            bool(evidence[key])
            for key in (
                "module_slot_activation_enabled",
                "capability_binding_activation_enabled",
                "dynamic_route_registration_enabled",
            )
        ):
            return self.build_check(
                "module_binding_safety",
                "blocked",
                evidence,
                summary="Module binding activation or route registration is enabled.",
            )
        return self.build_check(
            "module_binding_safety",
            "passed",
            evidence,
            summary="Module binding activation remains disabled.",
        )

    def _conformance_check(self, request: RCGateRunRequest) -> VerificationCheck:
        evidence = {
            "readiness_activation_enabled": self._settings.readiness_activation_enabled,
            "code_execution_enabled": self._settings.conformance_code_execution_enabled,
            "external_calls_enabled": self._settings.conformance_external_calls_enabled,
            "status": _jsonable(
                _safe_call(self._conformance_repository, "status", request.owner_scope)
            ),
        }
        if any(
            bool(evidence[key])
            for key in (
                "readiness_activation_enabled",
                "code_execution_enabled",
                "external_calls_enabled",
            )
        ):
            return self.build_check(
                "conformance_safety",
                "blocked",
                evidence,
                summary="Conformance activation or execution is enabled.",
            )
        return self.build_check(
            "conformance_safety", "passed", evidence, summary="Conformance remains metadata-only."
        )

    def _security_baseline_check(self, request: RCGateRunRequest) -> VerificationCheck:
        run = getattr(self._hardening_gate_service, "run", None)
        if callable(run):
            try:
                result = run(
                    HardeningGateRequest(
                        version=request.version or self._settings.version,
                        owner_scope=request.owner_scope,
                        include_secret_scan=False,
                        include_api_exposure_check=False,
                        include_policy_coverage_check=False,
                        created_by=request.created_by,
                        metadata={"source": "rc_gate"},
                    )
                )
                return self.build_check(
                    "security_baseline",
                    _status_from_result(result, pass_values={"passed", "warning"}),
                    _jsonable(result),
                    summary="Security baseline contributed local hardening status.",
                )
            except Exception as exc:
                return self._exception_check("security_baseline", exc)
        return self._missing_check("security_baseline")

    def _runtime_config_check(self, request: RCGateRunRequest) -> VerificationCheck:
        evidence = {
            "external_features_enabled": self._settings.bootstrap_enable_external_features,
            "external_model_default_enabled": self._settings.model_gateway_allow_external_default,
            "full_autonomy_enabled": self._settings.autonomy_default_max_mode == "full",
            "external_models_allowed": self._settings.autonomy_external_models_allowed_default,
            "external_tools_allowed": self._settings.autonomy_external_tools_allowed_default,
            "production_auth_enabled": not self._settings.dev_auth_enabled,
            "status": _jsonable(
                _safe_call(self._runtime_config_status_service, "status", request.owner_scope)
            ),
        }
        unsafe = any(
            bool(evidence[key])
            for key in (
                "external_features_enabled",
                "external_model_default_enabled",
                "full_autonomy_enabled",
                "external_models_allowed",
                "external_tools_allowed",
                "production_auth_enabled",
            )
        )
        if unsafe:
            return self.build_check(
                "runtime_config_safe",
                "blocked",
                evidence,
                summary="Unsafe runtime configuration blocks RC.",
            )
        return self.build_check(
            "runtime_config_safe",
            "passed",
            evidence,
            summary="Runtime configuration remains local-safe.",
        )

    def _operator_check(self, request: RCGateRunRequest) -> VerificationCheck:
        overview_request = OperatorOverviewRequest(
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
        )
        actor_context = _internal_actor_context(self._settings, request)
        overview = _safe_call(
            self._operator_service,
            "overview",
            overview_request,
            actor_context=actor_context,
        )
        if overview is None:
            overview = _safe_call(self._operator_service, "build_overview", request.owner_scope)
        return self.build_check(
            "operator_overview",
            "passed" if overview is not None else "warning",
            _jsonable(overview),
            summary="Operator overview is available."
            if overview is not None
            else "Operator overview unavailable.",
        )

    def _status_repository_check(self, check_key: str, source: object | None) -> VerificationCheck:
        status = _safe_call(source, "status", ["workspace:main"])
        if status is None:
            return self._missing_check(check_key)
        return self.build_check(check_key, _status_from_result(status), _jsonable(status))

    def _missing_check(self, check_key: str) -> VerificationCheck:
        return self.build_check(
            check_key,
            "warning",
            {"message": "service_unavailable"},
            summary=f"{check_key} service is unavailable.",
        )

    def _exception_check(self, check_key: str, exc: Exception) -> VerificationCheck:
        return self.build_check(
            check_key,
            "failed",
            {"error": exc.__class__.__name__},
            summary=f"{check_key} failed with {exc.__class__.__name__}.",
        )


def _normalize_check_status(status: str) -> VerificationCheckStatus:
    lowered = status.lower()
    if lowered in {"passed", "pass", "ok", "ready", "healthy", "completed", "dry_run"}:
        return "passed"
    if lowered in {"warning", "warn", "degraded"}:
        return "warning"
    if lowered in {"skipped", "skip"}:
        return "skipped"
    if lowered in {"blocked", "blocked_by_policy"}:
        return "blocked"
    if lowered in {"failed", "fail", "error", "critical"}:
        return "failed"
    return "unknown"


def _severity_for(status: VerificationCheckStatus, required: bool) -> VerificationSeverity:
    if status in {"failed", "blocked"}:
        return "critical" if required else "high"
    if status in {"warning", "unknown"}:
        return "high" if required else "medium"
    return "low"


def _title_for(check_key: str) -> str:
    return check_key.replace("_", " ").replace(".", " ").title()


def _summary_for(check_key: str, status: str) -> str:
    return f"{check_key} verification status is {status}."


def _status_from_result(result: object, *, pass_values: set[str] | None = None) -> str:
    allowed = pass_values or {"passed", "ready", "healthy", "ok", "completed", "dry_run"}
    if isinstance(result, dict):
        status = str(result.get("status") or result.get("overall_status") or "")
    else:
        status = str(getattr(result, "status", "") or getattr(result, "overall_status", ""))
    if status.lower() in allowed:
        return "passed"
    if status.lower() in {"warning", "degraded"}:
        return "warning"
    if status.lower() in {"blocked", "blocked_by_policy"}:
        return "blocked"
    if status.lower() in {"failed", "error", "critical"}:
        return "failed"
    return "unknown"


def _freeze_gate_status_from_result(result: object) -> str:
    status = _status_from_result(result, pass_values={"passed", "dry_run"})
    if status == "failed":
        return "failed"
    if isinstance(result, dict):
        report = result.get("report")
        failures = result.get("failures")
    else:
        report = getattr(result, "report", None)
        failures = getattr(result, "failures", None)
    if isinstance(report, dict) and report.get("release_ready") is True and not failures:
        return "passed"
    return status


def _safe_call(
    source: object | None, method_name: str, *args: object, **kwargs: object
) -> object | None:
    method = getattr(source, method_name, None)
    if not callable(method):
        return None
    try:
        return cast(object, method(*args, **kwargs))
    except TypeError:
        try:
            return cast(object, method())
        except Exception:
            return None
    except Exception:
        return None


def _jsonable(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return safe_rc_summary(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, dict):
            return safe_rc_summary(dumped)
    return safe_rc_summary({"value": str(value)})


def _internal_actor_context(settings: Settings, request: RCGateRunRequest) -> ActorContext | None:
    if settings.env != "development" or not settings.dev_auth_enabled:
        return None
    actor_id = request.actor_id or settings.default_dev_actor_id
    workspace_id = request.workspace_id or settings.default_dev_workspace_id
    return ActorContext(
        actor_id=actor_id,
        actor_type="system",
        workspace_id=workspace_id,
        roles=["owner"],
        permissions=["operator.overview.read"],
        security_scope=request.owner_scope,
        correlation_id=None,
        trace_id=request.trace_id,
        dev_mode=True,
    )


def _has_breaking_finding(value: object) -> bool:
    text = str(value).lower()
    return "breaking" in text and any(
        marker in text for marker in ("critical", "blocked", "failed")
    )


def _has_critical_marker(value: object) -> bool:
    text = str(value).lower()
    return "critical" in text and any(marker in text for marker in ("broken", "failed", "blocked"))


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = ["VerificationCheckCollector"]
