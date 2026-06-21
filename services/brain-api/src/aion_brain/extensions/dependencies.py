"""Extension dependency declaration service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.extensions import ExtensionDependencyDeclaration, ExtensionPackage
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository

_KNOWN_FEATURE_FLAGS = {
    "extensions.enabled",
    "extension_registry.enabled",
    "extension_manifest_validation.enabled",
    "extension_compatibility_gate.enabled",
    "extension_install_plans.enabled",
}


class DependencyDeclarationService:
    """Check declared dependencies without installing or downloading anything."""

    def __init__(
        self,
        repository: ExtensionRegistryRepository,
        policy_adapter: object,
        *,
        contract_repository: object | None = None,
        policy_catalog: object | None = None,
        runtime_config_status: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._contract_repository = contract_repository
        self._policy_catalog = policy_catalog
        self._runtime_config_status = runtime_config_status
        self._settings = settings

    def from_package(self, package: ExtensionPackage) -> list[ExtensionDependencyDeclaration]:
        """Convert package dependency metadata into declaration contracts."""

        declarations: list[ExtensionDependencyDeclaration] = []
        for item in package.declared_dependencies:
            dependency_key = str(item.get("dependency_key") or item.get("key") or "generic")
            dependency_type = str(item.get("dependency_type") or item.get("type") or "generic")
            declarations.append(
                ExtensionDependencyDeclaration(
                    dependency_declaration_id=f"extension-dependency-{uuid4().hex}",
                    extension_package_id=package.extension_package_id,
                    dependency_key=dependency_key,
                    dependency_type=cast(Any, dependency_type),
                    version_constraint=cast(str | None, item.get("version_constraint")),
                    required=bool(item.get("required", True)),
                    status="declared",
                    source=cast(Any, item.get("source") or "manifest"),
                    metadata={k: v for k, v in item.items() if k != "version_constraint"},
                    created_at=datetime.now(UTC),
                )
            )
        return declarations

    def check_dependencies(
        self,
        package: ExtensionPackage,
        declarations: list[ExtensionDependencyDeclaration],
    ) -> dict[str, Any]:
        """Return deterministic dependency availability result."""

        checks: list[dict[str, Any]] = []
        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        for declaration in declarations:
            status, reason = self._check_one(declaration, package.owner_scope)
            check = {
                "dependency_key": declaration.dependency_key,
                "dependency_type": declaration.dependency_type,
                "status": status,
                "reason": reason,
                "required": declaration.required,
            }
            checks.append(check)
            if declaration.required and status in {"missing", "blocked"}:
                blockers.append(check)
            elif status in {"missing", "blocked", "warning"}:
                warnings.append(check)
        return {
            "status": "blocked" if blockers else "warning" if warnings else "passed",
            "checks": checks,
            "blockers": blockers,
            "warnings": warnings,
        }

    def persist_declarations(
        self,
        package: ExtensionPackage,
        declarations: list[ExtensionDependencyDeclaration],
    ) -> list[ExtensionDependencyDeclaration]:
        authorize_extension_action(
            self._policy_adapter,
            "extension.package.update",
            package.owner_scope,
            actor_id=package.actor_id,
            workspace_id=package.workspace_id,
            trace_id=package.trace_id,
            resource_type="extension_dependency_declaration",
            resource_id=package.extension_package_id,
            risk_level="medium",
        )
        return [self._repository.save_dependency_declaration(item) for item in declarations]

    def list_for_package(
        self,
        extension_package_id: str,
        scope: list[str],
    ) -> list[ExtensionDependencyDeclaration]:
        authorize_extension_action(
            self._policy_adapter,
            "extension.dependency.read",
            scope,
            resource_type="extension_dependency_declaration",
            resource_id=extension_package_id,
            risk_level="low",
        )
        return self._repository.list_dependency_declarations(extension_package_id)

    def _check_one(
        self,
        declaration: ExtensionDependencyDeclaration,
        scope: list[str],
    ) -> tuple[str, str]:
        if declaration.dependency_type == "python_package_metadata":
            return "warning", "metadata_only_no_package_install"
        if declaration.dependency_type == "local_service":
            return "warning", "local_service_dependency_not_auto_started"
        if declaration.dependency_type == "aion_feature_flag":
            return self._check_feature_flag(declaration.dependency_key, scope)
        if declaration.dependency_type == "aion_setting":
            return self._check_setting(declaration.dependency_key)
        if declaration.dependency_type == "aion_policy_action":
            return self._check_policy_action(declaration.dependency_key)
        if declaration.dependency_type == "aion_contract":
            return self._check_contract(declaration.dependency_key)
        return "available", "generic_metadata_dependency"

    def _check_feature_flag(self, key: str, scope: list[str]) -> tuple[str, str]:
        status = getattr(self._runtime_config_status, "status", None)
        if callable(status):
            try:
                flags = status(scope).effective_feature_flags
                return (
                    ("available", "feature_flag_present")
                    if key in flags
                    else (
                        "missing",
                        "feature_flag_not_found",
                    )
                )
            except Exception:
                return "warning", "runtime_config_status_unavailable"
        return (
            ("available", "known_feature_flag")
            if key in _KNOWN_FEATURE_FLAGS
            else (
                "missing",
                "feature_flag_not_found",
            )
        )

    def _check_setting(self, key: str) -> tuple[str, str]:
        normalized = key.replace(".", "_")
        if self._settings is not None and hasattr(self._settings, normalized):
            return "available", "setting_present"
        return "missing", "setting_not_found"

    def _check_policy_action(self, key: str) -> tuple[str, str]:
        repository = getattr(self._policy_catalog, "_repository", None)
        get_action = getattr(repository, "get_action", None)
        if callable(get_action):
            try:
                return (
                    ("available", "policy_action_present")
                    if get_action(key)
                    else (
                        "missing",
                        "policy_action_not_found",
                    )
                )
            except Exception:
                return "warning", "policy_catalog_unavailable"
        if key.startswith("extension."):
            return "available", "extension_action_supported"
        return "warning", "policy_catalog_unavailable"

    def _check_contract(self, key: str) -> tuple[str, str]:
        list_contracts = getattr(self._contract_repository, "list_contracts", None)
        if not callable(list_contracts):
            return "warning", "contract_registry_unavailable"
        try:
            records = list_contracts(limit=1000)
        except Exception:
            return "warning", "contract_registry_unavailable"
        for record in records:
            if getattr(record, "contract_key", None) == key:
                return "available", "contract_present"
        return "missing", "contract_not_found"


__all__ = ["DependencyDeclarationService"]
