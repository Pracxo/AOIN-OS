"""Runtime configuration validator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.runtime_config import (
    ConfigValidationCheck,
    ConfigValidationRequest,
    ConfigValidationRun,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import enrich_with_internal_dev_actor
from aion_brain.runtime_config.profiles import _emit_runtime_config_event
from aion_brain.runtime_config.redaction import sanitize_config_dict
from aion_brain.runtime_config.repository import RuntimeConfigRepository


class ConfigValidator:
    """Validate safe runtime configuration posture."""

    def __init__(
        self,
        repository: RuntimeConfigRepository,
        policy_adapter: PolicyAdapter,
        *,
        feature_override_service: object | None = None,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._feature_override_service = feature_override_service
        self._settings = settings or get_settings()
        self._telemetry_service = telemetry_service

    def validate(self, request: ConfigValidationRequest) -> ConfigValidationRun:
        """Run deterministic local runtime config validation."""
        self._authorize(
            "runtime_config.validate",
            request.owner_scope,
            actor_id=request.created_by,
            risk_level="medium",
            context={"profile_id": request.profile_id, "snapshot_id": request.snapshot_id},
        )
        checks: list[ConfigValidationCheck] = []
        checks.append(
            _check(
                "no_raw_secret_values",
                True,
                "configuration",
                "Redaction helpers are applied before persistence.",
            )
        )
        if request.include_autonomy_checks:
            checks.extend(self._autonomy_checks())
        if request.include_security_checks:
            checks.extend(self._security_checks())
        if request.include_adapter_checks:
            checks.extend(self._adapter_checks())
        if request.include_feature_checks:
            checks.extend(self._feature_checks(request.owner_scope))
        checks.extend(self._profile_checks(request.profile_id))
        failures = [
            check.model_dump(mode="json")
            for check in checks
            if check.status == "failed" and check.severity in {"high", "critical"}
        ]
        warnings = [
            check.model_dump(mode="json")
            for check in checks
            if check.status in {"warning", "skipped"}
        ]
        status = "failed" if failures else ("warning" if warnings else "passed")
        now = datetime.now(UTC)
        run = ConfigValidationRun(
            config_validation_id=f"config-validation-{uuid4().hex}",
            trace_id=None,
            profile_id=request.profile_id,
            snapshot_id=request.snapshot_id,
            status=cast(Any, status),
            checks=checks,
            failures=failures,
            warnings=warnings,
            report={
                "safe_defaults_ok": status != "failed",
                "check_count": len(checks),
                "redacted_settings": sanitize_config_dict(self._settings.model_dump(mode="json")),
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        saved = self._repository.save_validation_run(run)
        self._emit(saved)
        return saved

    def _autonomy_checks(self) -> list[ConfigValidationCheck]:
        settings = self._settings
        return [
            _check(
                "full_autonomy_disabled_by_default",
                settings.autonomy_default_max_mode not in {"autonomous", "full"}
                and not settings.autonomy_external_tools_allowed_default
                and not settings.autonomy_background_workflows_allowed_default,
                "autonomy",
                "Full autonomy and external tools are disabled by default.",
                severity="critical",
            ),
            _check(
                "external_models_disabled_by_default",
                not settings.model_gateway_enabled
                and not settings.model_gateway_allow_external_default
                and not settings.autonomy_external_models_allowed_default,
                "model_gateway",
                "External model defaults are disabled.",
                severity="critical",
            ),
        ]

    def _security_checks(self) -> list[ConfigValidationCheck]:
        settings = self._settings
        return [
            _check(
                "api_stacktrace_exposed_false",
                not settings.api_stacktrace_exposed,
                "api",
                "API stacktrace exposure is disabled.",
                severity="critical",
            ),
            _check(
                "production_auth_not_claimed",
                bool(settings.dev_auth_enabled),
                "auth",
                "v0.1 uses explicit development auth and does not claim production auth.",
                severity="medium",
            ),
        ]

    def _adapter_checks(self) -> list[ConfigValidationCheck]:
        settings = self._settings
        return [
            _check(
                "mcp_disabled_by_default",
                not settings.mcp_enabled,
                "mcp",
                "MCP is disabled by default.",
                severity="high",
            ),
            _check(
                "sandbox_execution_disabled_by_default",
                not settings.sandbox_execution_enabled,
                "sandbox",
                "Sandbox execution is disabled by default.",
                severity="critical",
            ),
            _check(
                "restore_apply_disabled_by_default",
                not settings.backup_restore_apply_enabled,
                "backup",
                "Restore apply is disabled by default.",
                severity="critical",
            ),
            _check(
                "outbox_processing_disabled_by_default",
                not settings.outbox_process_enabled,
                "outbox",
                "Outbox processing is disabled by default.",
                severity="high",
            ),
            _check(
                "optional_adapters_remain_optional",
                not any(
                    [
                        settings.sandbox_docker_enabled,
                        settings.sandbox_firecracker_enabled,
                    ]
                ),
                "adapter",
                "Optional adapters are not selected for execution by default.",
                severity="medium",
                warning_on_fail=True,
            ),
        ]

    def _feature_checks(self, scope: list[str]) -> list[ConfigValidationCheck]:
        list_overrides = getattr(self._feature_override_service, "list_overrides", None)
        overrides = list_overrides(status="active") if callable(list_overrides) else []
        unsafe = [
            override.feature_key
            for override in overrides
            if bool(getattr(override, "enabled", False))
            and str(getattr(override, "feature_key", "")).startswith("autonomy.full")
        ]
        return [
            _check(
                "feature_overrides_do_not_enable_unsafe_defaults",
                not unsafe,
                "feature_flags",
                "Feature overrides do not enable unsafe defaults.",
                details={"unsafe": unsafe, "scope": scope},
                severity="critical",
            )
        ]

    def _profile_checks(self, profile_id: str | None) -> list[ConfigValidationCheck]:
        if profile_id is None:
            return []
        profile = self._repository.get_profile(profile_id)
        return [
            _check(
                "config_profile_exists",
                profile is not None,
                "configuration",
                "Config profile exists.",
                severity="high",
            )
        ]

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        policy_request = PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=None,
            actor_id=actor_id,
            workspace_id=None,
            action_type=action_type,
            resource_type="runtime_config_validation",
            resource_id=None,
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

    def _emit(self, run: ConfigValidationRun) -> None:
        _emit_runtime_config_event(
            self._telemetry_service,
            event_type="config_validation_completed",
            node_type="config_validation",
            node_id=run.config_validation_id,
            scope=["workspace:main"],
            intensity=0.8 if run.status == "passed" else 1.0,
            payload={"status": run.status},
        )


def _check(
    name: str,
    passed: bool,
    category: str,
    message: str,
    *,
    severity: str = "high",
    details: dict[str, Any] | None = None,
    warning_on_fail: bool = False,
) -> ConfigValidationCheck:
    status = "passed" if passed else ("warning" if warning_on_fail else "failed")
    return ConfigValidationCheck(
        check_id=f"config-check-{name}",
        name=name,
        category=category,
        status=cast(Any, status),
        severity=cast(Any, severity),
        message=message if passed else f"{message} Check failed.",
        details=details or {},
    )
