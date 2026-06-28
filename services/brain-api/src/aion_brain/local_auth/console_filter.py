"""Role-aware Operator Console view filtering."""

from __future__ import annotations

from aion_brain.contracts.local_auth import (
    ConsoleRoleFilterRequest,
    ConsoleRoleFilterResult,
    utc_now,
)
from aion_brain.local_auth.permission_matrix import RolePermissionMatrixService
from aion_brain.telemetry.visual import build_operator_console_telemetry_event


class ConsoleRoleFilter:
    """Filter console view models by local dev role without mutation."""

    def __init__(
        self,
        *,
        matrix_service: RolePermissionMatrixService | None = None,
        role_service: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        # role_service is accepted for AION-094 construction compatibility.
        self._matrix_service = matrix_service or _matrix_from_role_service(role_service)
        self._telemetry_service = telemetry_service

    def filter(self, request: ConsoleRoleFilterRequest) -> ConsoleRoleFilterResult:
        """Return a redacted read-only view model filtered by local roles."""
        filtered = self._matrix_service.filter_view_for_roles(
            request.view_model,
            request.auth_context.roles,
        )
        metadata = filtered.get("metadata")
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        forbidden_actions = _action_keys(filtered.get("forbidden_actions", []))
        result = ConsoleRoleFilterResult(
            status=(
                "filtered"
                if metadata_dict.get("removed_sections") or metadata_dict.get("removed_actions")
                else "unchanged"
            ),
            read_only=True,
            redaction_applied=True,
            actor_id=request.auth_context.actor_id,
            roles=request.auth_context.roles,
            filtered_view_model=filtered,
            removed_sections=list(metadata_dict.get("removed_sections", [])),
            removed_actions=list(metadata_dict.get("removed_actions", [])),
            forbidden_actions=forbidden_actions,
            safety_findings=list(metadata_dict.get("redaction_findings", [])),
            metadata={
                "no_write_actions_added": True,
                "forbidden_actions_visible": True,
                "write_allowed": False,
                "execute_allowed": False,
                "activation_allowed": False,
                "external_calls_allowed": False,
                "matrix_version": "aion-096",
            },
            created_at=utc_now(),
        )
        _emit(
            self._telemetry_service,
            "local_auth_console_filtered",
            "operator_console_view",
            str(filtered.get("console_view_model_id") or "local-auth-filtered-console"),
            request.auth_context.owner_scope,
            {"status": result.status, "roles": result.roles},
        )
        return result


def _matrix_from_role_service(role_service: object | None) -> RolePermissionMatrixService:
    matrix_service = getattr(role_service, "matrix_service", None)
    if isinstance(matrix_service, RolePermissionMatrixService):
        return matrix_service
    return RolePermissionMatrixService()


def _action_keys(actions: object) -> list[str]:
    if not isinstance(actions, list):
        return []
    return sorted(
        {
            str(action.get("action_key"))
            for action in actions
            if isinstance(action, dict) and action.get("action_key")
        }
    )


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


__all__ = ["ConsoleRoleFilter"]
