"""Deterministic module package validation."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.module_developer import (
    CapabilityCertificationCheck,
    ModulePackageCreateRequest,
    reject_secret_like_keys,
    validate_module_id,
)

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}
ALLOWED_EXECUTION_MODES = {"sync", "async", "scheduled", "streaming"}
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
PROVIDER_TERMS = {
    "openai",
    "anthropic",
    "gemini",
    "langchain",
    "langfuse",
    "bedrock",
    "vertex",
}
SHELL_KEYS = {"shell", "shell_command", "cmd", "exec", "subprocess", "system_command"}
SECRET_ENDPOINT_KEYS = {"endpoint_secret", "webhook_secret", "raw_secret"}


class ModulePackageValidator:
    """Validate package metadata and manifests without executing module code."""

    def validate_package(
        self,
        request: ModulePackageCreateRequest,
    ) -> list[CapabilityCertificationCheck]:
        """Validate package-level fields and its manifest."""

        checks = [
            _safe_check(
                "module_id_format",
                "schema",
                "critical",
                lambda: validate_module_id(request.module_id),
                "module_id is generic and accepted",
            ),
            _check(
                "version_present",
                "schema",
                bool(request.version.strip()),
                "version is present",
                "version is required",
                "critical",
            ),
            _payload_check("package_metadata_safe", request.metadata),
        ]
        checks.extend(self.validate_manifest(request.manifest))
        return checks

    def validate_manifest(self, manifest: CapabilityManifest) -> list[CapabilityCertificationCheck]:
        """Validate a capability manifest."""

        checks = [
            _safe_check(
                "manifest_module_id_format",
                "schema",
                "critical",
                lambda: validate_module_id(manifest.module_id),
                "manifest module_id is generic and accepted",
            ),
            _check(
                "manifest_version_present",
                "schema",
                bool(manifest.version.strip()),
                "manifest version is present",
                "manifest version is required",
                "critical",
            ),
            _check(
                "capability_list_non_empty",
                "schema",
                bool(manifest.capabilities),
                "capability list is non-empty",
                "capability list must not be empty",
                "critical",
            ),
            _check(
                "manifest_execution_mode_allowed",
                "runtime",
                manifest.execution_mode in ALLOWED_EXECUTION_MODES,
                "manifest execution_mode is supported",
                "manifest execution_mode is unsupported",
                "high",
            ),
        ]
        for capability in manifest.capabilities:
            checks.extend(self.validate_capability(capability))
        return checks

    def validate_capability(self, capability: dict[str, Any]) -> list[CapabilityCertificationCheck]:
        """Validate one capability dictionary."""

        capability_id = str(capability.get("capability_id") or capability.get("name") or "")
        risk_level = str(capability.get("risk_level") or "")
        permissions = capability.get("permissions_required", [])
        return [
            _check(
                f"{capability_id or 'capability'}_capability_id_safe",
                "schema",
                bool(capability_id.strip()) and not _contains_domain_term(capability_id),
                "capability_id is generic",
                "capability_id is missing or domain-specific",
                "critical",
            ),
            _check(
                f"{capability_id or 'capability'}_input_schema_dict",
                "schema",
                isinstance(capability.get("input_schema"), dict),
                "input_schema is a dict",
                "input_schema must be a dict",
                "critical",
            ),
            _check(
                f"{capability_id or 'capability'}_output_schema_dict",
                "schema",
                isinstance(capability.get("output_schema"), dict),
                "output_schema is a dict",
                "output_schema must be a dict",
                "critical",
            ),
            _check(
                f"{capability_id or 'capability'}_risk_level_allowed",
                "risk",
                risk_level in ALLOWED_RISK_LEVELS,
                "risk_level is supported",
                "risk_level is unsupported",
                "high",
            ),
            _check(
                f"{capability_id or 'capability'}_permissions_for_risk",
                "permissions",
                risk_level == "low" or (isinstance(permissions, list) and bool(permissions)),
                "permissions_required is acceptable",
                "non-low risk capabilities require permissions_required",
                "high",
            ),
            _check(
                f"{capability_id or 'capability'}_memory_read_scope_list",
                "memory_scope",
                isinstance(capability.get("memory_read_scopes", []), list),
                "memory_read_scopes is a list",
                "memory_read_scopes must be a list",
                "medium",
            ),
            _check(
                f"{capability_id or 'capability'}_memory_write_scope_list",
                "memory_scope",
                isinstance(capability.get("memory_write_scopes", []), list),
                "memory_write_scopes is a list",
                "memory_write_scopes must be a list",
                "medium",
            ),
            _check(
                f"{capability_id or 'capability'}_execution_mode_allowed",
                "runtime",
                str(capability.get("execution_mode") or "") in ALLOWED_EXECUTION_MODES,
                "execution_mode is supported",
                "execution_mode is unsupported",
                "high",
            ),
            _check(
                f"{capability_id or 'capability'}_timeout_positive",
                "runtime",
                int(capability.get("timeout_seconds") or 0) > 0,
                "timeout_seconds is positive",
                "timeout_seconds must be positive",
                "medium",
            ),
            _check(
                f"{capability_id or 'capability'}_audit_level_present",
                "audit",
                bool(str(capability.get("audit_level") or "").strip()),
                "audit_level is present",
                "audit_level is required",
                "high",
            ),
            _payload_check(f"{capability_id or 'capability'}_metadata_safe", capability),
        ]


def _payload_check(check_id: str, payload: dict[str, Any]) -> CapabilityCertificationCheck:
    failures: list[str] = []
    try:
        reject_secret_like_keys(payload)
    except ValueError as exc:
        failures.append(str(exc))
    if _contains_key(payload, SHELL_KEYS):
        failures.append("shell command fields are not allowed")
    if _contains_key(payload, SECRET_ENDPOINT_KEYS):
        failures.append("raw endpoint secrets are not allowed")
    if _contains_provider_term(payload):
        failures.append("provider SDK or vendor type names are not allowed")
    return _check(
        check_id,
        "boundary",
        not failures,
        "metadata and manifest payload are safe",
        "; ".join(failures) or "payload is unsafe",
        "critical",
        details={"failures": failures},
    )


def _safe_check(
    check_id: str,
    category: str,
    severity: str,
    action: object,
    success_message: str,
) -> CapabilityCertificationCheck:
    try:
        if callable(action):
            action()
    except ValueError as exc:
        return _check(
            check_id,
            category,
            False,
            success_message,
            str(exc),
            severity,
        )
    return _check(check_id, category, True, success_message, success_message, severity)


def _check(
    check_id: str,
    category: str,
    condition: bool,
    success_message: str,
    failure_message: str,
    severity: str,
    *,
    details: dict[str, Any] | None = None,
) -> CapabilityCertificationCheck:
    return CapabilityCertificationCheck(
        check_id=check_id,
        name=check_id.replace("_", " "),
        category=category,  # type: ignore[arg-type]
        status="passed" if condition else "failed",
        severity=severity,  # type: ignore[arg-type]
        message=success_message if condition else failure_message,
        details=details or {},
    )


def _contains_key(value: object, keys: set[str]) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in keys:
                return True
            if _contains_key(nested, keys):
                return True
    if isinstance(value, list):
        return any(_contains_key(item, keys) for item in value)
    return False


def _contains_provider_term(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_provider_term(key) or _contains_provider_term(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_contains_provider_term(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in PROVIDER_TERMS)
    return False


def _contains_domain_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in DOMAIN_TERMS)

