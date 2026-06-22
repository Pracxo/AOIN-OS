"""Deterministic local setup doctor."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from aion_brain.bootstrap.policy import authorize_bootstrap_action
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.bootstrap.telemetry import emit_bootstrap_telemetry
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.setup_doctor import SetupDoctorRequest, SetupDoctorResult, SetupFinding

_WEIGHTS = {
    "health_ready": 0.20,
    "policy_ready": 0.15,
    "sdk_ready": 0.10,
    "cli_ready": 0.10,
    "golden_path_ready": 0.20,
    "release_smoke_ready": 0.15,
    "docker_ready": 0.10,
}


class SetupDoctor:
    """Inspect local first-run readiness without subprocess calls."""

    def __init__(
        self,
        repository: BootstrapRepository,
        policy_adapter: object,
        *,
        diagnostics: object | None = None,
        golden_path_repository: object | None = None,
        release_smoke: object | None = None,
        operator_service: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
        root_dir: Path | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._diagnostics = diagnostics
        self._golden_path_repository = golden_path_repository
        self._release_smoke = release_smoke
        self._operator_service = operator_service
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._root_dir = root_dir or Path(__file__).parents[5]

    def run(self, request: SetupDoctorRequest) -> SetupDoctorResult:
        """Run setup readiness checks."""
        if not self._settings.setup_doctor_enabled:
            return _disabled_result(request.owner_scope)
        authorize_bootstrap_action(
            self._policy_adapter,
            "bootstrap.doctor.run",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="setup_doctor",
            risk_level="low",
            context={"external_calls": False, "shell_execution": False, **request.metadata},
        )
        self._emit(
            "setup_doctor_started",
            "setup_doctor",
            request.trace_id or f"setup-doctor-{uuid4().hex}",
            request.owner_scope,
            0.5,
            {},
        )
        findings: list[SetupFinding] = []
        checks_run: list[str] = []

        health_ready = self._check_health(request, findings, checks_run)
        policy_ready = self._check_policy(request, findings, checks_run)
        sdk_ready = self._check_sdk(request, findings, checks_run)
        cli_ready = self._check_cli(request, findings, checks_run)
        docker_ready = self._check_scripts(request, findings, checks_run)
        self._check_unsafe_features(request, findings, checks_run)
        golden_path_ready = (
            self._check_golden_path(request, findings, checks_run)
            if request.include_golden_path
            else True
        )
        release_smoke_ready = (
            self._check_release_smoke(request, findings, checks_run)
            if request.include_release_smoke
            else True
        )
        if self._operator_service is None:
            findings.append(
                _finding(
                    request,
                    "service_unavailable",
                    "operator",
                    "medium",
                    "operator_overview",
                    "Operator overview unavailable.",
                    "Operator Control Tower is not wired into this local app.",
                    "inspect_operator_overview",
                    expected={"available": True},
                    actual={"available": False},
                )
            )
        ready_flags = {
            "health_ready": health_ready,
            "policy_ready": policy_ready,
            "sdk_ready": sdk_ready,
            "cli_ready": cli_ready,
            "golden_path_ready": golden_path_ready,
            "release_smoke_ready": release_smoke_ready,
            "docker_ready": docker_ready,
        }
        readiness_score = round(
            sum(_WEIGHTS[key] for key, ready in ready_flags.items() if ready), 4
        )
        critical = [
            item for item in findings if item.severity == "critical" and item.status == "open"
        ]
        local_ready = (
            readiness_score >= self._settings.bootstrap_readiness_threshold
            and not critical
            and not findings
        )
        status = "passed" if local_ready else "failed" if critical else "warning"
        if request.create_findings:
            findings = [self._repository.save_finding(item) for item in findings]
        for item in findings:
            self._emit(
                "setup_finding_created",
                "setup_finding",
                item.setup_finding_id,
                item.owner_scope,
                1.0 if item.severity in {"high", "critical"} else 0.6,
                {"severity": item.severity, "category": item.category},
            )
        result = SetupDoctorResult(
            status=status,  # type: ignore[arg-type]
            owner_scope=request.owner_scope,
            checks_run=checks_run,
            findings=findings,
            readiness_score=readiness_score,
            local_ready=local_ready,
            health_ready=health_ready,
            policy_ready=policy_ready,
            sdk_ready=sdk_ready,
            cli_ready=cli_ready,
            golden_path_ready=golden_path_ready,
            release_smoke_ready=release_smoke_ready,
            docker_ready=docker_ready,
            recommendations=_recommendations(findings),
            metadata={
                "external_calls": False,
                "shell_execution": False,
                "package_install": False,
            },
            created_at=datetime.now(UTC),
        )
        self._emit(
            "setup_doctor_completed",
            "setup_doctor",
            request.trace_id or f"setup-doctor-{uuid4().hex}",
            request.owner_scope,
            result.readiness_score,
            {"status": result.status, "finding_count": len(result.findings)},
        )
        return result

    def _check_health(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> bool:
        checks_run.append("health")
        if self._diagnostics is None:
            findings.append(
                _finding(
                    request,
                    "service_unavailable",
                    "health",
                    "critical",
                    "health_diagnostics",
                    "Kernel diagnostics unavailable.",
                    "Health and readiness cannot be inspected through the kernel.",
                    "start_local_stack",
                    expected={"diagnostics": True},
                    actual={"diagnostics": False},
                )
            )
            return False
        return True

    def _check_policy(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> bool:
        checks_run.append("policy")
        if self._policy_adapter is None:
            findings.append(
                _finding(
                    request,
                    "policy_unavailable",
                    "policy",
                    "critical",
                    "policy_adapter",
                    "Policy adapter unavailable.",
                    "Bootstrap cannot run without policy evaluation.",
                    "inspect_policy_actions",
                    expected={"policy_adapter": True},
                    actual={"policy_adapter": False},
                )
            )
            return False
        return True

    def _check_sdk(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> bool:
        checks_run.append("sdk")
        path = self._root_dir / "packages/aion-sdk-python/src/aion_sdk/resources/bootstrap.py"
        if path.exists():
            return True
        findings.append(
            _finding(
                request,
                "sdk_missing",
                "sdk",
                "high",
                "sdk_bootstrap_resource",
                "Bootstrap SDK resource missing.",
                "The Python SDK does not expose BootstrapResource.",
                "inspect_operator_overview",
                expected={"path": path.as_posix(), "exists": True},
                actual={"exists": False},
            )
        )
        return False

    def _check_cli(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> bool:
        checks_run.append("cli")
        path = self._root_dir / "packages/aion-sdk-python/src/aion_sdk/cli/commands/bootstrap.py"
        if path.exists():
            return True
        findings.append(
            _finding(
                request,
                "cli_missing",
                "cli",
                "high",
                "cli_bootstrap_command",
                "Bootstrap CLI command missing.",
                "aionctl does not expose the bootstrap command group.",
                "inspect_operator_overview",
                expected={"path": path.as_posix(), "exists": True},
                actual={"exists": False},
            )
        )
        return False

    def _check_scripts(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> bool:
        checks_run.append("scripts")
        ok = True
        for script in (
            "scripts/check.sh",
            "scripts/golden-path.sh",
            "scripts/release-smoke.sh",
            "scripts/bootstrap-local.sh",
            "scripts/setup-doctor.sh",
            "scripts/seed-defaults.sh",
        ):
            path = self._root_dir / script
            if not path.exists():
                ok = False
                findings.append(
                    _finding(
                        request,
                        "script_missing",
                        "scripts",
                        "medium",
                        script,
                        "Local setup script missing.",
                        f"{script} is not present in the repo.",
                        "run_setup_doctor",
                        expected={"exists": True},
                        actual={"exists": False},
                    )
                )
            elif not path.stat().st_mode & 0o111:
                ok = False
                findings.append(
                    _finding(
                        request,
                        "script_not_executable",
                        "scripts",
                        "medium",
                        script,
                        "Local setup script is not executable.",
                        f"{script} exists but is not executable.",
                        "run_setup_doctor",
                        expected={"executable": True},
                        actual={"executable": False},
                    )
                )
        return ok

    def _check_unsafe_features(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> None:
        checks_run.append("unsafe_defaults")
        unsafe_settings = {
            "bootstrap_enable_external_features": self._settings.bootstrap_enable_external_features,
            "model_gateway_allow_external_default": getattr(
                self._settings, "model_gateway_allow_external_default", False
            ),
            "external_notifications_enabled": getattr(
                self._settings, "external_notifications_enabled", False
            ),
            "extension_code_loading_enabled": getattr(
                self._settings, "extension_code_loading_enabled", False
            ),
            "extension_external_sources_enabled": getattr(
                self._settings, "extension_external_sources_enabled", False
            ),
            "capability_binding_activation_enabled": getattr(
                self._settings, "capability_binding_activation_enabled", False
            ),
            "lifecycle_hard_delete_enabled": getattr(
                self._settings, "lifecycle_hard_delete_enabled", False
            ),
            "autonomy_external_models_allowed_default": getattr(
                self._settings, "autonomy_external_models_allowed_default", False
            ),
            "autonomy_external_tools_allowed_default": getattr(
                self._settings, "autonomy_external_tools_allowed_default", False
            ),
        }
        for key, enabled in unsafe_settings.items():
            if enabled:
                findings.append(
                    _finding(
                        request,
                        "external_feature_enabled",
                        "config",
                        "critical",
                        key,
                        "Unsafe external feature enabled.",
                        f"{key} must remain disabled for v0.1 local bootstrap.",
                        "inspect_operator_overview",
                        expected={key: False},
                        actual={key: True},
                    )
                )

    def _check_golden_path(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> bool:
        checks_run.append("golden_path")
        latest_report = _try_call(self._golden_path_repository, "latest_report")
        if bool(getattr(latest_report, "release_candidate_ready", False)):
            return True
        findings.append(
            _finding(
                request,
                "golden_path_failed",
                "golden_path",
                "medium",
                "golden_path_latest",
                "Golden path has not passed yet.",
                "Run the local golden path dry-run before release readiness.",
                "run_golden_path",
                expected={"release_candidate_ready": True},
                actual={"release_candidate_ready": False},
            )
        )
        return False

    def _check_release_smoke(
        self,
        request: SetupDoctorRequest,
        findings: list[SetupFinding],
        checks_run: list[str],
    ) -> bool:
        checks_run.append("release_smoke")
        if self._release_smoke is None:
            findings.append(
                _finding(
                    request,
                    "release_smoke_failed",
                    "release_smoke",
                    "medium",
                    "release_smoke_service",
                    "Release smoke matrix unavailable.",
                    "The local release smoke service is not wired.",
                    "run_release_smoke",
                    expected={"available": True},
                    actual={"available": False},
                )
            )
            return False
        latest_report = _try_call(self._golden_path_repository, "latest_report")
        return bool(getattr(latest_report, "release_candidate_ready", False))

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


def _finding(
    request: SetupDoctorRequest,
    finding_type: str,
    category: str,
    severity: str,
    check_key: str,
    title: str,
    description: str,
    recommended_action: str,
    *,
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> SetupFinding:
    return SetupFinding(
        setup_finding_id=f"setup-finding-{uuid4().hex}",
        trace_id=request.trace_id,
        finding_type=finding_type,  # type: ignore[arg-type]
        category=category,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        status="open",
        title=title,
        description=description,
        check_key=check_key,
        expected=expected,
        actual=actual,
        recommended_action=recommended_action,
        owner_scope=request.owner_scope,
        metadata={},
        created_at=datetime.now(UTC),
    )


def _recommendations(findings: list[SetupFinding]) -> list[str]:
    if not findings:
        return ["run_golden_path", "run_release_smoke", "run_freeze_gate", "run_release_package"]
    ordered = []
    for item in findings:
        if item.recommended_action not in ordered:
            ordered.append(item.recommended_action)
    return ordered


def _disabled_result(scope: list[str]) -> SetupDoctorResult:
    return SetupDoctorResult(
        status="failed",
        owner_scope=scope,
        checks_run=[],
        findings=[],
        readiness_score=0.0,
        local_ready=False,
        health_ready=False,
        policy_ready=False,
        sdk_ready=False,
        cli_ready=False,
        golden_path_ready=False,
        release_smoke_ready=False,
        docker_ready=False,
        recommendations=["run_setup_doctor"],
        metadata={"disabled": True},
        created_at=datetime.now(UTC),
    )


def _try_call(source: object | None, method_name: str) -> object | None:
    method = getattr(source, method_name, None)
    if not callable(method):
        return None
    try:
        result: object = method()
        return result
    except Exception:
        return None


__all__ = ["SetupDoctor"]
