"""Extension capability declaration service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.extensions import ExtensionCapabilityDeclaration, ExtensionPackage
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.extensions.repository import ExtensionRegistryRepository

_VALID_CAPABILITY_TYPES = {
    "reasoning",
    "retrieval",
    "memory",
    "evidence",
    "planning",
    "execution",
    "workflow",
    "connector",
    "adapter",
    "visualization",
    "policy",
    "operator",
    "generic",
}
_VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


class CapabilityDeclarationService:
    """Validate and persist declared capabilities without activating them."""

    def __init__(
        self,
        repository: ExtensionRegistryRepository,
        policy_adapter: object,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def from_package(self, package: ExtensionPackage) -> list[ExtensionCapabilityDeclaration]:
        """Convert package capability metadata into declaration contracts."""

        declarations: list[ExtensionCapabilityDeclaration] = []
        for item in package.declared_capabilities:
            capability_key = str(
                item.get("capability_key")
                or item.get("capability_id")
                or f"{package.extension_key}.capability"
            )
            capability_type = str(item.get("capability_type") or item.get("type") or "generic")
            risk_level = str(item.get("risk_level") or "medium")
            declarations.append(
                ExtensionCapabilityDeclaration(
                    capability_declaration_id=f"extension-capability-{uuid4().hex}",
                    extension_package_id=package.extension_package_id,
                    capability_key=capability_key,
                    capability_type=cast(Any, capability_type),
                    status="declared",
                    risk_level=cast(Any, risk_level),
                    requires_policy=bool(item.get("requires_policy", True)),
                    requires_approval=bool(
                        item.get("requires_approval", risk_level in {"high", "critical"})
                    ),
                    requires_sandbox=bool(
                        item.get("requires_sandbox", risk_level in {"high", "critical"})
                    ),
                    dry_run_supported=bool(item.get("dry_run_supported", True)),
                    controlled_supported=bool(item.get("controlled_supported", False)),
                    input_schema=dict(item.get("input_schema") or {}),
                    output_schema=dict(item.get("output_schema") or {}),
                    constraints=list(item.get("constraints") or []),
                    metadata={
                        k: v
                        for k, v in item.items()
                        if k not in {"input_schema", "output_schema"}
                    },
                    created_at=datetime.now(UTC),
                )
            )
        return declarations

    def validate_declarations(
        self,
        declarations: list[ExtensionCapabilityDeclaration],
    ) -> dict[str, Any]:
        """Return blockers and warnings for declaration metadata."""

        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        for declaration in declarations:
            if declaration.capability_type not in _VALID_CAPABILITY_TYPES:
                blockers.append(_finding("invalid_capability_type", declaration.capability_key))
            if declaration.risk_level not in _VALID_RISK_LEVELS:
                blockers.append(_finding("invalid_risk_level", declaration.capability_key))
            if declaration.risk_level in {"high", "critical"}:
                if not declaration.requires_policy:
                    blockers.append(
                        _finding("high_risk_without_policy", declaration.capability_key)
                    )
                if not declaration.requires_approval:
                    blockers.append(
                        _finding("high_risk_without_approval", declaration.capability_key)
                    )
                if not declaration.requires_sandbox:
                    blockers.append(
                        _finding("high_risk_without_sandbox", declaration.capability_key)
                    )
            if declaration.controlled_supported:
                warnings.append(
                    _finding(
                        "controlled_capability_declaration_only",
                        declaration.capability_key,
                        severity="medium",
                    )
                )
        return {
            "status": "blocked" if blockers else "warning" if warnings else "passed",
            "blockers": blockers,
            "warnings": warnings,
            "declaration_count": len(declarations),
        }

    def persist_declarations(
        self,
        package: ExtensionPackage,
        declarations: list[ExtensionCapabilityDeclaration],
    ) -> list[ExtensionCapabilityDeclaration]:
        authorize_extension_action(
            self._policy_adapter,
            "extension.package.update",
            package.owner_scope,
            actor_id=package.actor_id,
            workspace_id=package.workspace_id,
            trace_id=package.trace_id,
            resource_type="extension_capability_declaration",
            resource_id=package.extension_package_id,
            risk_level="medium",
        )
        return [self._repository.save_capability_declaration(item) for item in declarations]

    def list_for_package(
        self,
        extension_package_id: str,
        scope: list[str],
    ) -> list[ExtensionCapabilityDeclaration]:
        authorize_extension_action(
            self._policy_adapter,
            "extension.capability_declaration.read",
            scope,
            resource_type="extension_capability_declaration",
            resource_id=extension_package_id,
            risk_level="low",
        )
        return self._repository.list_capability_declarations(extension_package_id)


def _finding(code: str, capability_key: str, severity: str = "high") -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "capability_key": capability_key,
        "message": f"Capability declaration {capability_key} failed {code}.",
    }


__all__ = ["CapabilityDeclarationService"]
