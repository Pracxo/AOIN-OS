"""Role-aware connector credential authorization matrix."""

from __future__ import annotations

from aion_brain.connector_credentials.denials import DENIED_CREDENTIAL_ACTIONS
from aion_brain.contracts.connector_credentials import ConnectorCredentialAuthorizationEntry
from aion_brain.dialogue._shared import emit_telemetry

PREVIEW_CREDENTIAL_ACTIONS = (
    "connector_credentials.boundary.read",
    "connector_credentials.lifecycle.read",
    "connector_credentials.authorization.read",
    "connector_credentials.readiness.preview",
    "connector_credentials.redaction.preview",
    "connector_credentials.status.read",
)
READ_ACTIONS = {
    "connector_credentials.boundary.read",
    "connector_credentials.lifecycle.read",
    "connector_credentials.authorization.read",
    "connector_credentials.status.read",
}
PREVIEW_ACTIONS = set(PREVIEW_CREDENTIAL_ACTIONS) - READ_ACTIONS
ROLES = ("viewer", "operator", "reviewer", "admin", "auditor")


class ConnectorCredentialAuthorizationService:
    """Build credential authorization entries with material access denied."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def list_entries(self) -> list[ConnectorCredentialAuthorizationEntry]:
        """Return role/action decisions with storage and material access denied."""

        entries: list[ConnectorCredentialAuthorizationEntry] = []
        for role in ROLES:
            for action_key in PREVIEW_CREDENTIAL_ACTIONS:
                entries.append(_preview_entry(role, action_key))
            for action_key in DENIED_CREDENTIAL_ACTIONS:
                entries.append(_denied_entry(role, action_key))
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_credential_authorization_read",
            node_type="connector_credential_authorization",
            node_id="connector-credential-authorization-local",
            intensity=0.5,
            trace_id="connector-credential-authorization-local",
            payload={"entry_count": len(entries), "credential_access_allowed": False},
        )
        return entries

    def find(
        self,
        *,
        role: str,
        action_key: str,
    ) -> ConnectorCredentialAuthorizationEntry | None:
        """Return the matrix row for a role/action pair."""

        normalized_role = role.strip().lower()
        for entry in self.list_entries():
            if entry.role == normalized_role and entry.action_key == action_key:
                return entry
        return None


def _preview_entry(role: str, action_key: str) -> ConnectorCredentialAuthorizationEntry:
    can_read = action_key in READ_ACTIONS and role in ROLES
    can_preview = action_key in PREVIEW_ACTIONS and role in {"operator", "reviewer", "admin"}
    allowed = can_read or can_preview
    return ConnectorCredentialAuthorizationEntry(
        role=role,
        action_key=action_key,
        decision="allow_read" if can_read else "allow_preview" if can_preview else "deny",
        credential_access_allowed=False,
        token_access_allowed=False,
        secret_material_allowed=False,
        storage_allowed=False,
        rotation_allowed=False,
        revocation_allowed=False,
        audit_required=True,
        review_required=action_key in PREVIEW_ACTIONS,
        reason=(
            "read_only_connector_credential_action"
            if can_read
            else "connector_credential_preview_action"
            if allowed
            else "role_not_allowed_for_connector_credential_action"
        ),
        metadata={"preview_only": True, "credential_storage_enabled": False},
    )


def _denied_entry(role: str, action_key: str) -> ConnectorCredentialAuthorizationEntry:
    return ConnectorCredentialAuthorizationEntry(
        role=role,
        action_key=action_key,
        decision="deny",
        credential_access_allowed=False,
        token_access_allowed=False,
        secret_material_allowed=False,
        storage_allowed=False,
        rotation_allowed=False,
        revocation_allowed=False,
        audit_required=True,
        review_required=True,
        reason="future_connector_credential_action_blocked",
        metadata={"denied_future_action": True, "credential_storage_enabled": False},
    )


__all__ = [
    "ConnectorCredentialAuthorizationService",
    "PREVIEW_CREDENTIAL_ACTIONS",
    "READ_ACTIONS",
    "ROLES",
]
