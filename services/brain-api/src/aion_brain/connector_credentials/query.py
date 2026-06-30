"""Connector credential query helpers."""

from __future__ import annotations

from typing import Any

from aion_brain.connector_credentials.architecture import ConnectorCredentialArchitectureService
from aion_brain.connector_credentials.authorization import ConnectorCredentialAuthorizationService
from aion_brain.connector_credentials.denials import ConnectorCredentialDenialService
from aion_brain.connector_credentials.lifecycle import ConnectorCredentialLifecycleService


class ConnectorCredentialQueryService:
    """Expose read-only connector credential status and query evidence."""

    def __init__(
        self,
        *,
        architecture_service: ConnectorCredentialArchitectureService,
        lifecycle_service: ConnectorCredentialLifecycleService,
        authorization_service: ConnectorCredentialAuthorizationService,
        denial_service: ConnectorCredentialDenialService,
        settings: object | None = None,
    ) -> None:
        self._architecture_service = architecture_service
        self._lifecycle_service = lifecycle_service
        self._authorization_service = authorization_service
        self._denial_service = denial_service
        self._settings = settings

    def query(self, payload: dict[str, Any], owner_scope: list[str]) -> dict[str, Any]:
        """Return connector credential query evidence without material access."""

        action = payload.get("action_key")
        action_key = str(action).strip() if isinstance(action, str) else None
        return {
            "status": "preview",
            "owner_scope": owner_scope,
            "boundary": self._architecture_service.boundary().model_dump(mode="json"),
            "lifecycle": [
                state.model_dump(mode="json") for state in self._lifecycle_service.list_states()
            ],
            "authorization": [
                entry.model_dump(mode="json")
                for entry in self._authorization_service.list_entries()
                if action_key is None or entry.action_key == action_key
            ],
            "denial": self._denial_service.denial_for(action_key or "") if action_key else None,
            "credential_storage_allowed": False,
            "token_storage_allowed": False,
            "credential_access_allowed": False,
            "token_access_allowed": False,
            "secret_material_present": False,
            "external_identity_runtime_allowed": False,
        }

    def status(self, owner_scope: list[str]) -> dict[str, Any]:
        """Return connector credential status for a scope."""

        return {
            "status": "enabled",
            "read_only": True,
            "design_only": True,
            "readiness_preview_only": True,
            "owner_scope": owner_scope,
            "connector_credentials_architecture_enabled": bool(
                getattr(self._settings, "connector_credentials_architecture_enabled", True)
            ),
            "connector_credentials_readiness_enabled": bool(
                getattr(self._settings, "connector_credentials_readiness_enabled", True)
            ),
            "connector_credentials_redaction_preview_enabled": bool(
                getattr(self._settings, "connector_credentials_redaction_preview_enabled", True)
            ),
            "connector_credentials_storage_enabled": False,
            "connector_tokens_storage_enabled": False,
            "connector_secret_material_enabled": False,
            "connector_external_identity_runtime_enabled": False,
            "connector_runtime_credential_access_enabled": False,
            "credential_storage_allowed": False,
            "token_storage_allowed": False,
            "credential_access_allowed": False,
            "token_access_allowed": False,
            "secret_material_present": False,
            "external_identity_runtime_allowed": False,
            "denied_action_count": len(self._denial_service.denied_actions()),
        }


__all__ = ["ConnectorCredentialQueryService"]
