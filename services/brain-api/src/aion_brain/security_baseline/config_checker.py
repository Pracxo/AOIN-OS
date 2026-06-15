"""Local configuration hardening checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from aion_brain.config import Settings, get_settings

_RAW_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*[\"']?[A-Za-z0-9._~+/=-]{12,}"
)


class ConfigHardeningChecker:
    """Inspect local settings and repository config for unsafe defaults."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        root_dir: Path | None = None,
        config_validator: object | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._root_dir = root_dir or Path(__file__).parents[5]
        self._config_validator = config_validator

    def check(self) -> list[dict[str, Any]]:
        """Return deterministic config hardening checks."""
        compose = self._root_dir / "docker-compose.yml"
        checks = [
            _check(
                ".env_not_committed",
                not (self._root_dir / ".env").exists(),
                "configuration",
            ),
            _check(
                ".env_example_exists",
                (self._root_dir / ".env.example").exists(),
                "configuration",
            ),
            _check(
                "external_models_disabled_by_default",
                not self._settings.model_gateway_enabled
                and not self._settings.model_gateway_allow_external_default
                and not self._settings.autonomy_external_models_allowed_default,
                "model_gateway",
            ),
            _check("mcp_disabled_by_default", not self._settings.mcp_enabled, "mcp"),
            _check(
                "sandbox_execution_disabled_by_default",
                not self._settings.sandbox_execution_enabled,
                "sandbox",
            ),
            _check(
                "restore_apply_disabled_by_default",
                not self._settings.backup_restore_apply_enabled,
                "backup",
            ),
            _check(
                "full_autonomy_disabled_by_default",
                self._settings.autonomy_default_max_mode not in {"autonomous", "full"}
                and not self._settings.autonomy_external_tools_allowed_default
                and not self._settings.autonomy_background_workflows_allowed_default,
                "autonomy",
            ),
            _check(
                "outbox_process_disabled_by_default",
                not self._settings.outbox_process_enabled,
                "configuration",
            ),
            _check(
                "optional_adapters_disabled_by_default",
                not any(
                    (
                        self._settings.turbovec_enabled,
                        self._settings.graphiti_enabled,
                        self._settings.temporal_enabled,
                        self._settings.sandbox_docker_enabled,
                        self._settings.sandbox_firecracker_enabled,
                    )
                ),
                "configuration",
            ),
            _check(
                "api_stacktrace_exposed_false",
                not self._settings.api_stacktrace_exposed,
                "api",
            ),
            _check(
                "production_auth_not_claimed",
                self._settings.dev_auth_enabled or self._settings.env != "production",
                "auth",
                severity="warning",
            ),
            _check(
                "docker_compose_has_no_raw_secrets",
                _file_has_no_raw_secret(compose),
                "configuration",
            ),
            _check(
                "no_cloud_deployment_config",
                not any((self._root_dir / name).exists() for name in ("terraform", "pulumi")),
                "configuration",
                severity="warning",
            ),
        ]
        runtime_validation = self._runtime_config_validation_check()
        if runtime_validation is not None:
            checks.append(runtime_validation)
        return checks

    def _runtime_config_validation_check(self) -> dict[str, Any] | None:
        validate = getattr(self._config_validator, "validate", None)
        if not callable(validate):
            return None
        from aion_brain.contracts.runtime_config import ConfigValidationRequest

        try:
            result = validate(
                ConfigValidationRequest(
                    owner_scope=["workspace:main"],
                    include_security_checks=True,
                    include_autonomy_checks=True,
                    include_adapter_checks=True,
                    include_feature_checks=True,
                    metadata={"source": "config_hardening_checker"},
                )
            )
        except Exception as exc:
            return _check(
                "runtime_config_validation_available",
                False,
                "configuration",
                severity="warning",
                details={"reason": exc.__class__.__name__},
            )
        return _check(
            "runtime_config_validation_passed",
            result.status in {"passed", "warning"},
            "configuration",
            severity="critical",
            details={"status": result.status, "validation_id": result.config_validation_id},
        )


def _check(
    name: str,
    passed: bool,
    category: str,
    *,
    severity: str = "high",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "status": "passed" if passed else "failed",
        "severity": severity,
        "message": f"{name} {'passed' if passed else 'failed'}.",
        "details": details or {},
    }


def _file_has_no_raw_secret(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return True
    for line in text.splitlines():
        if "AION_SECRET_SCAN_IGNORE" in line:
            continue
        if _RAW_SECRET_ASSIGNMENT.search(line):
            return False
    return True
