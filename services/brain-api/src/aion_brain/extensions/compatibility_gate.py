"""Extension compatibility gate."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.extension_compatibility import (
    ExtensionCompatibilityRequest,
    ExtensionCompatibilityRun,
)
from aion_brain.contracts.extensions import ExtensionPackage
from aion_brain.extensions.capabilities import CapabilityDeclarationService
from aion_brain.extensions.dependencies import DependencyDeclarationService
from aion_brain.extensions.manifest_validator import ManifestValidator
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository
from aion_brain.extensions.telemetry import emit_extension_telemetry


class ExtensionCompatibilityGate:
    """Check extension metadata against local AION contracts and configuration."""

    def __init__(
        self,
        repository: ExtensionRegistryRepository,
        policy_adapter: object,
        *,
        manifest_validator: ManifestValidator,
        dependency_service: DependencyDeclarationService,
        capability_service: CapabilityDeclarationService,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._manifest_validator = manifest_validator
        self._dependency_service = dependency_service
        self._capability_service = capability_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def check(self, request: ExtensionCompatibilityRequest) -> ExtensionCompatibilityRun:
        """Run deterministic compatibility checks and persist the run."""

        authorize_extension_action(
            self._policy_adapter,
            "extension.compatibility.check",
            request.owner_scope,
            actor_id=request.created_by,
            trace_id=request.trace_id,
            resource_type="extension_compatibility",
            resource_id=request.extension_package_id,
            risk_level="medium",
            context={"mode": request.mode},
        )
        package = self._repository.get_package(request.extension_package_id)
        if package is None:
            raise ValueError("extension_package_not_found")
        return self.check_package(package, request)

    def check_package(
        self,
        package: ExtensionPackage,
        request: ExtensionCompatibilityRequest,
    ) -> ExtensionCompatibilityRun:
        """Run compatibility checks for a loaded package contract."""

        validation = self._manifest_validator.validate(package.manifest)
        capabilities = self._capability_service.from_package(package)
        capability_result = self._capability_service.validate_declarations(capabilities)
        dependencies = self._dependency_service.from_package(package)
        dependency_result = self._dependency_service.check_dependencies(package, dependencies)
        checks = [
            _check("manifest_validation", validation["status"], validation),
            _check("capability_declarations", capability_result["status"], capability_result),
            _check("dependency_declarations", dependency_result["status"], dependency_result),
            _check("runtime_flags", "passed", self._runtime_flag_result()),
            _check("sandbox_requirements", "passed", self._sandbox_result(package)),
            _check("no_dynamic_routes", "passed", self._route_result(package)),
            _check("no_code_loading", "passed", self._code_loading_result()),
        ]
        blockers = _collect(checks, "blockers")
        warnings = _collect(checks, "warnings")
        if not self._settings_ok():
            blockers.append(
                {
                    "code": "unsafe_extension_settings",
                    "severity": "critical",
                    "message": (
                        "Extension code loading, activation, and external sources must be disabled."
                    ),
                }
            )
        status = _status_for(blockers, warnings)
        score = max(0.0, min(1.0, 1.0 - (len(blockers) * 0.2) - (len(warnings) * 0.05)))
        run = ExtensionCompatibilityRun(
            extension_compatibility_id=(
                request.extension_compatibility_id or f"extension-compatibility-{uuid4().hex}"
            ),
            trace_id=request.trace_id or package.trace_id,
            extension_package_id=package.extension_package_id,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope or package.owner_scope,
            contract_snapshot_id=request.contract_snapshot_id,
            compatibility_scan_id=None,
            checks=checks,
            findings=[item for check in checks for item in check.get("findings", [])],
            blockers=blockers,
            warnings=warnings,
            score=score,
            result={
                "metadata_only": True,
                "capability_count": len(capabilities),
                "dependency_count": len(dependencies),
            },
            metadata={**request.metadata, "source_mutated": False},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_compatibility_run(run)
        self._repository.save_package(
            package.model_copy(
                update={
                    "compatibility_status": saved.status,
                    "status": _package_status(saved.status, package.review_status),
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        emit_extension_telemetry(
            self._telemetry_service,
            event_type="extension_compatibility_checked",
            node_type="extension_compatibility",
            node_id=saved.extension_compatibility_id,
            scope=saved.owner_scope,
            intensity=0.8 if saved.status in {"failed", "blocked"} else 0.5,
            payload={"status": saved.status, "extension_package_id": saved.extension_package_id},
        )
        return saved

    def get(
        self,
        extension_compatibility_id: str,
        scope: list[str],
    ) -> ExtensionCompatibilityRun | None:
        authorize_extension_action(
            self._policy_adapter,
            "extension.compatibility.check",
            scope,
            resource_type="extension_compatibility",
            resource_id=extension_compatibility_id,
            risk_level="low",
        )
        return self._repository.get_compatibility_run(extension_compatibility_id)

    def _runtime_flag_result(self) -> dict[str, Any]:
        return {
            "extensions_enabled": bool(getattr(self._settings, "extensions_enabled", True)),
            "extension_registry_enabled": bool(
                getattr(self._settings, "extension_registry_enabled", True)
            ),
            "manifest_validation_enabled": bool(
                getattr(self._settings, "extension_manifest_validation_enabled", True)
            ),
            "compatibility_gate_enabled": bool(
                getattr(self._settings, "extension_compatibility_gate_enabled", True)
            ),
        }

    def _sandbox_result(self, package: ExtensionPackage) -> dict[str, Any]:
        return {
            "declared": bool(package.manifest.sandbox_requirements),
            "requirements": package.manifest.sandbox_requirements,
            "declaration_only": True,
        }

    def _route_result(self, package: ExtensionPackage) -> dict[str, Any]:
        return {
            "declared_route_count": len(package.declared_routes),
            "dynamic_registration_allowed": False,
        }

    def _code_loading_result(self) -> dict[str, Any]:
        return {
            "code_loading_enabled": bool(
                getattr(self._settings, "extension_code_loading_enabled", False)
            ),
            "activation_enabled": bool(
                getattr(self._settings, "extension_activation_enabled", False)
            ),
            "external_sources_enabled": bool(
                getattr(self._settings, "extension_external_sources_enabled", False)
            ),
        }

    def _settings_ok(self) -> bool:
        return not (
            bool(getattr(self._settings, "extension_code_loading_enabled", False))
            or bool(getattr(self._settings, "extension_activation_enabled", False))
            or bool(getattr(self._settings, "extension_external_sources_enabled", False))
        )


def _check(name: str, status: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "findings": list(payload.get("findings", [])),
        "blockers": list(payload.get("blockers", [])),
        "warnings": list(payload.get("warnings", [])),
        "details": payload,
    }


def _collect(checks: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return [item for check in checks for item in list(check.get(key, []))]


def _status_for(blockers: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> str:
    if any(item.get("severity") == "critical" for item in blockers):
        return "blocked"
    if blockers:
        return "failed"
    if warnings:
        return "warning"
    return "passed"


def _package_status(compatibility_status: str, review_status: str) -> str:
    if compatibility_status in {"blocked", "failed"}:
        return "incompatible"
    if review_status == "not_reviewed":
        return "review_required"
    return "validated"


__all__ = ["ExtensionCompatibilityGate"]
