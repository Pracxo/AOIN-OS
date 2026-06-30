"""Role-aware connector policy authorization matrix."""

from __future__ import annotations

from aion_brain.connector_policy.catalog import DENIED_ACTION_KEYS, PREVIEW_ACTION_KEYS
from aion_brain.contracts.connector_policy import ConnectorAuthorizationMatrixEntry
from aion_brain.dialogue._shared import emit_telemetry

READ_ACTIONS = {
    "connector_runtime.status.read",
    "connector_simulator.status.read",
    "connector_simulator.query",
    "connector_policy.catalog.read",
    "connector_policy.matrix.read",
    "connector_policy.traceability.read",
}
DRY_RUN_ACTIONS = set(PREVIEW_ACTION_KEYS) - READ_ACTIONS
ROLES = ("viewer", "operator", "reviewer", "admin", "auditor")


class ConnectorAuthorizationMatrixService:
    """Build a deterministic authorization matrix for connector policy actions."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def list_entries(self) -> list[ConnectorAuthorizationMatrixEntry]:
        """Return role/action decisions with runtime permissions hard-disabled."""

        entries: list[ConnectorAuthorizationMatrixEntry] = []
        for role in ROLES:
            for action_key in PREVIEW_ACTION_KEYS:
                entries.append(_preview_entry(role, action_key))
            for action_key in DENIED_ACTION_KEYS:
                entries.append(_denied_entry(role, action_key))
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_authorization_matrix_read",
            node_type="connector_authorization_matrix",
            node_id="connector-authorization-matrix-local",
            intensity=0.5,
            trace_id="connector-authorization-matrix-local",
            payload={"entry_count": len(entries), "runtime_allowed": False},
        )
        return entries

    def find(self, *, role: str, action_key: str) -> ConnectorAuthorizationMatrixEntry | None:
        """Return the matrix row for a role/action pair."""

        normalized_role = role.strip().lower()
        for entry in self.list_entries():
            if entry.role == normalized_role and entry.action_key == action_key:
                return entry
        return None


def _preview_entry(role: str, action_key: str) -> ConnectorAuthorizationMatrixEntry:
    can_read = action_key in READ_ACTIONS and role in {
        "viewer",
        "operator",
        "reviewer",
        "admin",
        "auditor",
    }
    can_dry_run = action_key in DRY_RUN_ACTIONS and role in {"operator", "reviewer", "admin"}
    allowed = can_read or can_dry_run
    return ConnectorAuthorizationMatrixEntry(
        role=role,
        action_key=action_key,
        decision="allow_read" if can_read else "allow_dry_run" if can_dry_run else "deny",
        reason=(
            "read_only_connector_policy_action"
            if can_read
            else "connector_policy_dry_run_preview"
            if can_dry_run
            else "role_not_allowed_for_connector_policy_action"
        ),
        dry_run_allowed=allowed,
        runtime_allowed=False,
        external_call_allowed=False,
        credential_access_allowed=False,
        token_access_allowed=False,
        activation_allowed=False,
        review_required=action_key in DRY_RUN_ACTIONS,
        audit_required=True,
        metadata={"preview_only": True, "runtime_allowed": False},
    )


def _denied_entry(role: str, action_key: str) -> ConnectorAuthorizationMatrixEntry:
    return ConnectorAuthorizationMatrixEntry(
        role=role,
        action_key=action_key,
        decision="deny",
        reason="future_connector_runtime_action_blocked",
        dry_run_allowed=False,
        runtime_allowed=False,
        external_call_allowed=False,
        credential_access_allowed=False,
        token_access_allowed=False,
        activation_allowed=False,
        review_required=True,
        audit_required=True,
        metadata={"denied_future_action": True, "runtime_allowed": False},
    )


__all__ = ["ConnectorAuthorizationMatrixService", "DRY_RUN_ACTIONS", "READ_ACTIONS", "ROLES"]
