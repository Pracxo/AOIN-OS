"""Deterministic sandbox validation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from pydantic import ValidationError

from aion_brain.config import Settings
from aion_brain.contracts.sandbox import (
    RuntimePermissionGrant,
    SandboxProfile,
    SandboxRunRequest,
    SandboxValidationCheck,
    SandboxValidationResult,
)
from aion_brain.secrets.redaction import reject_secret_like_keys, reject_secret_like_values

DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "hr",
    "procurement",
    "payments",
}


class SandboxValidator:
    """Validate sandbox profiles, runs, and runtime grants without execution."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate_profile(self, profile: SandboxProfile) -> SandboxValidationResult:
        """Validate one sandbox profile."""
        checks = [
            _check(
                "profile_active",
                profile.status == "active",
                "profile is active",
                "profile is not active",
                "medium",
            ),
            _check(
                "sandbox_type_supported",
                profile.sandbox_type
                in {"local_noop", "docker", "firecracker", "external_placeholder"},
                "sandbox type is supported by contract",
                "sandbox type is unsupported",
                "critical",
            ),
            _check(
                "docker_firecracker_execution_disabled",
                profile.sandbox_type not in {"docker", "firecracker"}
                or not self._settings.sandbox_execution_enabled,
                "placeholder sandbox type is not executable",
                "docker and firecracker execution are disabled in v0.1",
                "medium",
                warning=True,
            ),
            _check(
                "process_spawn_disabled",
                not profile.process_spawn_enabled,
                "process spawn is disabled",
                "process spawn is denied in v0.1",
                "critical",
            ),
            _check(
                "network_internal_only",
                _network_safe(profile),
                "network is disabled or limited to internal egress",
                "network egress is not internal-only",
                "high",
            ),
            _check(
                "wildcard_egress_denied",
                not any(rule.destination_type == "wildcard" for rule in profile.egress_rules),
                "wildcard egress is denied",
                "wildcard egress is denied in v0.1",
                "critical",
            ),
            _check(
                "filesystem_write_disabled",
                not profile.filesystem_write_enabled,
                "filesystem write is disabled",
                "filesystem write is denied by default",
                "high",
            ),
            _check(
                "resource_limits_valid",
                _valid_resource_limits(profile),
                "resource limits are within bounds",
                "resource limits are invalid",
                "critical",
            ),
            _payload_check("profile_metadata_safe", profile.metadata),
            _check(
                "filesystem_rules_safe",
                _filesystem_rules_safe(profile),
                "filesystem rules are safe",
                "filesystem rules include host escape or Docker socket",
                "critical",
            ),
            _check(
                "permissions_domain_neutral",
                not _contains_domain_term(
                    [permission.permission for permission in profile.allowed_runtime_permissions]
                ),
                "runtime permissions are domain-neutral",
                "runtime permissions contain domain-specific terms",
                "high",
            ),
        ]
        return _result(
            sandbox_profile_id=profile.sandbox_profile_id,
            target_type="sandbox_profile",
            target_id=profile.sandbox_profile_id,
            checks=checks,
            metadata={"sandbox_type": profile.sandbox_type},
        )

    def validate_run(
        self,
        request: SandboxRunRequest,
        profile: SandboxProfile,
    ) -> SandboxValidationResult:
        """Validate one sandbox run request against its profile."""
        checks = [
            *_clone_checks(self.validate_profile(profile).checks),
            _check(
                "run_profile_active",
                profile.status == "active",
                "sandbox profile is active",
                "sandbox profile is disabled",
                "critical",
            ),
            _check(
                "run_profile_matches",
                request.sandbox_profile_id == profile.sandbox_profile_id,
                "request profile matches loaded profile",
                "request profile mismatch",
                "critical",
            ),
            _check(
                "docker_firecracker_run_disabled",
                profile.sandbox_type not in {"docker", "firecracker"},
                "run does not target docker or firecracker execution",
                "docker and firecracker execution are unsupported in v0.1",
                "critical",
            ),
            _check(
                "controlled_execution_disabled",
                request.mode == "dry_run" or self._settings.sandbox_execution_enabled,
                "controlled execution is disabled or not requested",
                "controlled sandbox execution is disabled",
                "high",
                warning=True,
            ),
            _payload_check("run_input_safe", request.input),
            _payload_check("run_metadata_safe", request.metadata),
        ]
        return _result(
            sandbox_profile_id=profile.sandbox_profile_id,
            target_type=request.target_type,
            target_id=request.target_id,
            checks=checks,
            metadata={"mode": request.mode},
        )

    def validate_runtime_permissions(
        self,
        grant: RuntimePermissionGrant,
    ) -> SandboxValidationResult:
        """Validate explicit runtime permission grants."""
        permissions = [str(permission.permission) for permission in grant.permissions]
        checks = [
            _check(
                "runtime_permissions_present",
                bool(grant.permissions),
                "runtime permissions are explicit",
                "runtime permissions must not be empty",
                "critical",
            ),
            _check(
                "secret_refs_explicit",
                all(ref.strip() for ref in grant.secret_refs),
                "secret refs are explicit",
                "secret refs must be explicit",
                "high",
            ),
            _check(
                "connector_refs_explicit",
                all(ref.strip() for ref in grant.connector_refs),
                "connector refs are explicit",
                "connector refs must be explicit",
                "high",
            ),
            _check(
                "process_spawn_not_granted",
                "runtime.process.spawn" not in permissions,
                "process spawn is not granted",
                "process spawn grants are denied in v0.1",
                "critical",
            ),
            _check(
                "permissions_domain_neutral",
                not _contains_domain_term(permissions),
                "runtime permissions are domain-neutral",
                "runtime permissions contain domain-specific terms",
                "high",
            ),
            _payload_check("runtime_permission_metadata_safe", grant.metadata),
        ]
        return _result(
            sandbox_profile_id=grant.sandbox_profile_id,
            target_type=grant.target_type,
            target_id=grant.target_id,
            checks=checks,
            metadata={"runtime_permission_id": grant.runtime_permission_id},
        )


def _check(
    check_id: str,
    condition: bool,
    success_message: str,
    failure_message: str,
    severity: str,
    *,
    warning: bool = False,
    details: dict[str, Any] | None = None,
) -> SandboxValidationCheck:
    status = "passed" if condition else "warning" if warning else "failed"
    return SandboxValidationCheck(
        check_id=check_id,
        name=check_id.replace("_", " "),
        status=cast(Any, status),
        severity=cast(Any, severity),
        message=success_message if condition else failure_message,
        details=details or {},
    )


def _payload_check(check_id: str, payload: dict[str, Any]) -> SandboxValidationCheck:
    failures: list[str] = []
    try:
        reject_secret_like_keys(payload)
        reject_secret_like_values(payload)
    except ValueError as exc:
        failures.append(str(exc))
    return _check(
        check_id,
        not failures,
        "payload contains no secret-like material",
        "; ".join(failures) or "payload is unsafe",
        "critical",
        details={"failures": failures},
    )


def _result(
    *,
    sandbox_profile_id: str | None,
    target_type: str,
    target_id: str | None,
    checks: list[SandboxValidationCheck],
    metadata: dict[str, Any],
) -> SandboxValidationResult:
    failed = [check for check in checks if check.status == "failed"]
    warnings = [check for check in checks if check.status == "warning"]
    status = "failed" if _has_critical_failure(checks) else "warning" if warnings else "passed"
    score = sum(check.status == "passed" for check in checks) / len(checks) if checks else 0.0
    return SandboxValidationResult(
        validation_id=f"sandbox-validation-{uuid4().hex}",
        sandbox_profile_id=sandbox_profile_id,
        target_type=target_type,
        target_id=target_id,
        status=cast(Any, status),
        score=score,
        checks=checks,
        failures=[check.model_dump(mode="json") for check in failed],
        warnings=[check.model_dump(mode="json") for check in warnings],
        metadata=metadata,
        created_at=datetime.now(UTC),
    )


def _has_critical_failure(checks: list[SandboxValidationCheck]) -> bool:
    return any(
        check.status == "failed" and check.severity in {"high", "critical"} for check in checks
    )


def _network_safe(profile: SandboxProfile) -> bool:
    if not profile.network_enabled:
        return True
    return bool(profile.egress_rules) and all(
        rule.destination_type in {"none", "internal"} for rule in profile.egress_rules
    )


def _valid_resource_limits(profile: SandboxProfile) -> bool:
    try:
        ResourceLimits = type(profile.resource_limits)
        ResourceLimits.model_validate(profile.resource_limits.model_dump(mode="python"))
    except (TypeError, ValueError, ValidationError):
        return False
    return True


def _filesystem_rules_safe(profile: SandboxProfile) -> bool:
    try:
        for rule in profile.filesystem_rules:
            rule.model_validate(rule.model_dump(mode="python"))
    except (TypeError, ValueError, ValidationError):
        return False
    return True


def _contains_domain_term(values: list[str]) -> bool:
    for value in values:
        normalized = value.lower().replace("_", ".").replace("-", ".")
        if any(f".{term}." in f".{normalized}." for term in DOMAIN_TERMS):
            return True
    return False


def _clone_checks(checks: list[SandboxValidationCheck]) -> list[SandboxValidationCheck]:
    return [check.model_copy() for check in checks]
