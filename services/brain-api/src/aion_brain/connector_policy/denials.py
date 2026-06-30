"""Connector policy denial rules."""

from __future__ import annotations

from aion_brain.connector_policy.catalog import DENIED_ACTION_KEYS


class ConnectorPolicyDenialService:
    """Return explicit denial reasons for future connector runtime actions."""

    def denied_actions(self) -> set[str]:
        """Return denied future/runtime connector actions."""

        return set(DENIED_ACTION_KEYS)

    def denial_for(self, action_key: str) -> dict[str, object] | None:
        """Return denial metadata for an action key."""

        if action_key not in self.denied_actions():
            return None
        return {
            "action_key": action_key,
            "decision": "deny",
            "reason": "future_connector_runtime_action_blocked",
            "runtime_allowed": False,
            "external_call_allowed": False,
            "credential_access_allowed": False,
            "token_access_allowed": False,
            "activation_allowed": False,
            "audit_required": True,
            "provenance_required": True,
        }


__all__ = ["ConnectorPolicyDenialService"]
