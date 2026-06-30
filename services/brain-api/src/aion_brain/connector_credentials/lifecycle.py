"""Connector credential lifecycle model."""

from __future__ import annotations

from aion_brain.contracts.connector_credentials import ConnectorCredentialLifecycleState
from aion_brain.dialogue._shared import emit_telemetry

LIFECYCLE_STATE_KEYS = (
    "requested",
    "approved_for_future_storage",
    "provisioned_future",
    "rotated_future",
    "revoked_future",
    "expired_future",
    "quarantined_future",
    "deleted_future",
)


class ConnectorCredentialLifecycleService:
    """Expose future credential lifecycle states without implementing storage."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def list_states(self) -> list[ConnectorCredentialLifecycleState]:
        """Return credential lifecycle states with storage states future-only."""

        states = [_state(key) for key in LIFECYCLE_STATE_KEYS]
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_credential_lifecycle_read",
            node_type="connector_credential_lifecycle",
            node_id="connector-credential-lifecycle-local",
            intensity=0.45,
            trace_id="connector-credential-lifecycle-local",
            payload={"state_count": len(states), "storage_enabled": False},
        )
        return states


def _state(state_key: str) -> ConnectorCredentialLifecycleState:
    is_request = state_key == "requested"
    return ConnectorCredentialLifecycleState(
        state_key=state_key,
        title=state_key.replace("_", " ").title(),
        description="Future connector credential lifecycle state; no material is stored today.",
        allowed_today=is_request,
        future_only=not is_request,
        requires_production_auth=not is_request,
        requires_secret_store=not is_request,
        requires_rotation_plan=state_key in {"approved_for_future_storage", "rotated_future"},
        requires_revocation_plan=state_key
        in {"approved_for_future_storage", "revoked_future", "quarantined_future"},
        requires_audit=True,
        requires_provenance=True,
        blockers=[
            {"blocker_key": "production_auth_required", "bypassable": False},
            {"blocker_key": "credential_store_absent", "bypassable": False},
            {"blocker_key": "token_store_absent", "bypassable": False},
        ]
        if not is_request
        else [{"blocker_key": "design_review_only", "bypassable": False}],
        metadata={
            "credential_storage_enabled": False,
            "token_storage_enabled": False,
            "secret_material_present": False,
        },
    )


__all__ = ["ConnectorCredentialLifecycleService", "LIFECYCLE_STATE_KEYS"]
