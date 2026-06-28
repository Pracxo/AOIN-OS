"""Dev-only identity simulation service."""

from __future__ import annotations

from aion_brain.contracts.local_auth import DevIdentitySimulationRequest, LocalAuthContext
from aion_brain.local_auth.context import build_local_auth_context
from aion_brain.local_auth.identity import build_local_operator_identity
from aion_brain.local_auth.roles import LocalRoleService
from aion_brain.telemetry.visual import build_operator_console_telemetry_event


class DevIdentitySimulator:
    """Create synthetic local auth contexts without authentication."""

    def __init__(
        self,
        *,
        role_service: LocalRoleService | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._role_service = role_service or LocalRoleService()
        self._telemetry_service = telemetry_service

    def simulate(self, request: DevIdentitySimulationRequest) -> LocalAuthContext:
        """Return a synthetic non-privileged local auth context."""
        identity = build_local_operator_identity(request)
        context = build_local_auth_context(
            identity,
            trace_id=request.trace_id,
            role_service=self._role_service,
        )
        _emit(
            self._telemetry_service,
            "local_auth_context_simulated",
            "local_auth_context",
            context.local_auth_context_id,
            context.owner_scope,
            {
                "roles": context.roles,
                "production_auth": False,
                "local_session_preview_compatible": True,
            },
        )
        return context


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    scope: list[str],
    payload: dict[str, object] | None = None,
) -> None:
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    emit(
        build_operator_console_telemetry_event(
            telemetry_id=f"telemetry-{node_id}",
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            payload=payload,
        )
    )


__all__ = ["DevIdentitySimulator"]
