"""Connector credential store architecture boundary."""

from __future__ import annotations

from aion_brain.contracts.connector_credentials import ConnectorCredentialBoundary, utc_now
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorCredentialArchitectureService:
    """Return a local-only credential architecture boundary without storage."""

    def __init__(self, *, telemetry_service: object | None = None) -> None:
        self._telemetry_service = telemetry_service

    def boundary(self) -> ConnectorCredentialBoundary:
        """Return the current connector credential boundary."""

        boundary = ConnectorCredentialBoundary(
            credential_boundary_id="connector-credential-boundary-aion-113",
            name="Connector Credential Store Architecture Boundary",
            description="Design-only credential boundary; no credential or token storage exists.",
            credential_storage_enabled=False,
            token_storage_enabled=False,
            secret_material_present=False,
            plaintext_secret_allowed=False,
            browser_secret_storage_allowed=False,
            log_secret_allowed=False,
            external_identity_runtime_enabled=False,
            connector_runtime_credential_access_enabled=False,
            rotation_required=True,
            revocation_required=True,
            audit_required=True,
            provenance_required=True,
            blockers=[
                {"blocker_key": "credential_store_absent", "bypassable": False},
                {"blocker_key": "token_store_absent", "bypassable": False},
                {"blocker_key": "secret_material_absent", "bypassable": False},
                {"blocker_key": "external_identity_runtime_absent", "bypassable": False},
                {"blocker_key": "connector_runtime_disabled", "bypassable": False},
            ],
            metadata={
                "design_only": True,
                "readiness_preview_only": True,
                "credential_storage_enabled": False,
                "token_storage_enabled": False,
                "secret_material_present": False,
                "external_identity_runtime_enabled": False,
                "connector_runtime_credential_access_enabled": False,
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_credential_boundary_read",
            node_type="connector_credential_boundary",
            node_id=boundary.credential_boundary_id,
            intensity=0.45,
            trace_id=boundary.credential_boundary_id,
            payload={"credential_storage_enabled": False, "token_storage_enabled": False},
        )
        return boundary


__all__ = ["ConnectorCredentialArchitectureService"]
