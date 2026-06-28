"""Role access audit service for local console filtering."""

from __future__ import annotations

from aion_brain.contracts.local_auth import RoleAccessAudit
from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService
from aion_brain.telemetry.visual import build_operator_console_telemetry_event


class RoleAccessAuditService:
    """Audit the local role matrix without creating privileged grants."""

    def __init__(
        self,
        *,
        matrix_service: RolePermissionMatrixService | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._matrix_service = matrix_service or RolePermissionMatrixService()
        self._telemetry_service = telemetry_service

    def audit(self, trace_id: str | None = None) -> RoleAccessAudit:
        """Return a read-only role access audit report."""
        result = self._matrix_service.audit_matrix(trace_id=trace_id)
        _emit(
            self._telemetry_service,
            "local_auth_role_access_audited",
            "local_auth_role_matrix",
            result.role_access_audit_id,
            ["workspace:main"],
            {"status": result.status},
        )
        return result


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


__all__ = ["RoleAccessAuditService"]
