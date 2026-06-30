"""Connector sandbox denial rules."""

from __future__ import annotations

from aion_brain.connector_sandbox.capabilities import DENIED_CAPABILITY_KEYS


class ConnectorSandboxDenialService:
    """Return explicit denials for future sandbox runtime capabilities."""

    def denied_capabilities(self) -> set[str]:
        """Return denied sandbox capability keys."""

        return set(DENIED_CAPABILITY_KEYS)

    def denial_for(self, capability_key: str) -> dict[str, object] | None:
        """Return denial metadata for a sandbox capability key."""

        if capability_key not in self.denied_capabilities():
            return None
        return {
            "capability_key": capability_key,
            "decision": "deny",
            "reason": "future_connector_sandbox_capability_blocked",
            "runtime_execution_allowed": False,
            "filesystem_access_allowed": False,
            "network_access_allowed": False,
            "credential_access_allowed": False,
            "token_access_allowed": False,
            "process_spawn_allowed": False,
            "dynamic_import_allowed": False,
            "package_install_allowed": False,
            "connector_activation_allowed": False,
            "audit_required": True,
            "provenance_required": True,
        }


__all__ = ["ConnectorSandboxDenialService"]
