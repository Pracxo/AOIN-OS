"""Connector credential denial rules."""

from __future__ import annotations

DENIED_CREDENTIAL_ACTIONS = (
    "connector.credentials.store",
    "connector.credentials.read",
    "connector.credentials.rotate",
    "connector.credentials.revoke",
    "connector.tokens.store",
    "connector.tokens.read",
    "connector.secrets.materialize",
    "connector.oauth.callback",
    "connector.oauth.exchange",
    "connector.oidc.login",
    "connector.saml.assertion",
    "connector.external_identity.bind",
)


class ConnectorCredentialDenialService:
    """Return explicit denials for future credential, token, and identity actions."""

    def denied_actions(self) -> set[str]:
        """Return denied connector credential action keys."""

        return set(DENIED_CREDENTIAL_ACTIONS)

    def denial_for(self, action_key: str) -> dict[str, object] | None:
        """Return denial metadata for a connector credential action key."""

        if action_key not in self.denied_actions():
            return None
        return {
            "action_key": action_key,
            "decision": "deny",
            "reason": "future_connector_credential_action_blocked",
            "credential_storage_allowed": False,
            "token_storage_allowed": False,
            "credential_access_allowed": False,
            "token_access_allowed": False,
            "secret_material_allowed": False,
            "external_identity_runtime_allowed": False,
            "connector_runtime_credential_access_allowed": False,
            "audit_required": True,
            "provenance_required": True,
        }


__all__ = ["DENIED_CREDENTIAL_ACTIONS", "ConnectorCredentialDenialService"]
