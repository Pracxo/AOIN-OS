"""Connector policy status query helpers."""

from __future__ import annotations

from typing import Any

from aion_brain.connector_policy.catalog import ConnectorPolicyCatalogService
from aion_brain.connector_policy.denials import ConnectorPolicyDenialService
from aion_brain.connector_policy.matrix import ConnectorAuthorizationMatrixService


class ConnectorPolicyQueryService:
    """Expose read-only connector policy status."""

    def __init__(
        self,
        *,
        catalog_service: ConnectorPolicyCatalogService,
        matrix_service: ConnectorAuthorizationMatrixService,
        denial_service: ConnectorPolicyDenialService,
        settings: object | None = None,
    ) -> None:
        self._catalog_service = catalog_service
        self._matrix_service = matrix_service
        self._denial_service = denial_service
        self._settings = settings

    def status(self, owner_scope: list[str]) -> dict[str, Any]:
        """Return connector policy status for a scope."""

        actions = self._catalog_service.list_actions(include_denied=True)
        matrix = self._matrix_service.list_entries()
        return {
            "status": "enabled",
            "read_only": True,
            "dry_run_only": True,
            "owner_scope": owner_scope,
            "connector_policy_catalog_enabled": bool(
                getattr(self._settings, "connector_policy_catalog_enabled", True)
            ),
            "connector_policy_dry_run_enabled": bool(
                getattr(self._settings, "connector_policy_dry_run_enabled", True)
            ),
            "connector_policy_runtime_allow_enabled": False,
            "connector_policy_external_calls_enabled": False,
            "connector_policy_credentials_enabled": False,
            "connector_policy_tokens_enabled": False,
            "connector_policy_activation_enabled": False,
            "connector_runtime_enabled": False,
            "action_count": len(actions),
            "matrix_entry_count": len(matrix),
            "denied_action_count": len(self._denial_service.denied_actions()),
        }


__all__ = ["ConnectorPolicyQueryService"]
