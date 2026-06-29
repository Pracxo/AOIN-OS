"""Disabled external connector runtime gate service."""

from __future__ import annotations

from aion_brain.connector_runtime.blockers import disabled_runtime_blockers
from aion_brain.contracts.connector_runtime import ConnectorRuntimeStatus, utc_now
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorRuntimeGateService:
    """Expose disabled connector-runtime status without enabling connector behavior."""

    def __init__(
        self,
        *,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._settings = settings
        self._telemetry_service = telemetry_service

    def status(self, scope: list[str]) -> ConnectorRuntimeStatus:
        """Return disabled external connector runtime status for one scope."""

        status = ConnectorRuntimeStatus(
            status_id="connector-runtime-status-local",
            connector_runtime_enabled=bool(
                getattr(self._settings, "connector_runtime_enabled", False)
            ),
            connector_mock_preview_enabled=bool(
                getattr(self._settings, "connector_mock_preview_enabled", True)
            ),
            connector_egress_preview_enabled=bool(
                getattr(self._settings, "connector_egress_preview_enabled", True)
            ),
            connector_ingress_preview_enabled=bool(
                getattr(self._settings, "connector_ingress_preview_enabled", True)
            ),
            connector_external_calls_enabled=bool(
                getattr(self._settings, "connector_external_calls_enabled", False)
            ),
            connector_credentials_enabled=bool(
                getattr(self._settings, "connector_credentials_enabled", False)
            ),
            connector_token_storage_enabled=bool(
                getattr(self._settings, "connector_token_storage_enabled", False)
            ),
            connector_activation_enabled=bool(
                getattr(self._settings, "connector_activation_enabled", False)
            ),
            connector_route_registration_enabled=bool(
                getattr(self._settings, "connector_route_registration_enabled", False)
            ),
            blockers=disabled_runtime_blockers(),
            warnings=[{"code": "connector_runtime_disabled", "status": "open"}],
            metadata={
                "disabled_by_default": True,
                "owner_scope": scope,
                "mock_only": True,
                "network_calls_allowed": False,
                "runtime_activation_allowed": False,
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_runtime_status_checked",
            node_type="connector_runtime_status",
            node_id=status.status_id,
            intensity=0.65,
            trace_id=status.status_id,
            payload={
                "connector_runtime_enabled": False,
                "connector_external_calls_enabled": False,
                "connector_mock_preview_enabled": status.connector_mock_preview_enabled,
            },
        )
        return status


__all__ = ["ConnectorRuntimeGateService"]
