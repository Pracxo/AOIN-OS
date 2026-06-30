"""Connector sandbox query helpers."""

from __future__ import annotations

from typing import Any

from aion_brain.connector_sandbox.capabilities import ConnectorSandboxCapabilityRuleService
from aion_brain.connector_sandbox.denials import ConnectorSandboxDenialService
from aion_brain.connector_sandbox.isolation import ConnectorIsolationBoundaryService


class ConnectorSandboxQueryService:
    """Expose read-only connector sandbox status and query evidence."""

    def __init__(
        self,
        *,
        boundary_service: ConnectorIsolationBoundaryService,
        capability_service: ConnectorSandboxCapabilityRuleService,
        denial_service: ConnectorSandboxDenialService,
        settings: object | None = None,
    ) -> None:
        self._boundary_service = boundary_service
        self._capability_service = capability_service
        self._denial_service = denial_service
        self._settings = settings

    def query(self, payload: dict[str, Any], owner_scope: list[str]) -> dict[str, Any]:
        """Return connector sandbox query evidence without sandbox execution."""

        capability = payload.get("capability")
        capability_key = str(capability).strip() if isinstance(capability, str) else None
        return {
            "status": "preview",
            "owner_scope": owner_scope,
            "boundary": self._boundary_service.boundary().model_dump(mode="json"),
            "rules": [
                rule.model_dump(mode="json")
                for rule in self._capability_service.list_rules(include_denied=True)
                if capability_key is None or rule.rule_key == capability_key
            ],
            "denial": self._denial_service.denial_for(capability_key or "")
            if capability_key
            else None,
            "runtime_execution_allowed": False,
            "filesystem_access_allowed": False,
            "network_access_allowed": False,
            "credential_access_allowed": False,
            "token_access_allowed": False,
            "process_spawn_allowed": False,
            "dynamic_import_allowed": False,
            "package_install_allowed": False,
            "connector_activation_allowed": False,
        }

    def status(self, owner_scope: list[str]) -> dict[str, Any]:
        """Return connector sandbox status for a scope."""

        rules = self._capability_service.list_rules(include_denied=True)
        return {
            "status": "enabled",
            "read_only": True,
            "design_only": True,
            "readiness_preview_only": True,
            "owner_scope": owner_scope,
            "connector_sandbox_design_enabled": bool(
                getattr(self._settings, "connector_sandbox_design_enabled", True)
            ),
            "connector_sandbox_readiness_enabled": bool(
                getattr(self._settings, "connector_sandbox_readiness_enabled", True)
            ),
            "connector_sandbox_runtime_execution_enabled": False,
            "connector_sandbox_filesystem_enabled": False,
            "connector_sandbox_network_enabled": False,
            "connector_sandbox_credentials_enabled": False,
            "connector_sandbox_tokens_enabled": False,
            "connector_sandbox_process_spawn_enabled": False,
            "connector_sandbox_dynamic_import_enabled": False,
            "connector_sandbox_package_install_enabled": False,
            "connector_sandbox_activation_enabled": False,
            "connector_runtime_enabled": False,
            "rule_count": len(rules),
            "denied_capability_count": len(self._denial_service.denied_capabilities()),
        }


__all__ = ["ConnectorSandboxQueryService"]
